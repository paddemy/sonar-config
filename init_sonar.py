import requests
import sys
import time

# === CONFIGURACIÓN ===
SONAR_URL = "http://localhost:9000"
OLD_ADMIN_PASSWORD = "admin"
NEW_ADMIN_PASSWORD = "$4adminP@ssw0rd"
TOKEN_NAME = "dev_token"
QUALITY_GATE_NAME = "Paddemy Local Quality Gate"
QUALITY_PROFILE_NAME = "Paddemy Local Java Rules"
PROJECT_KEY = "paddemy_backend_key"
PROJECT_NAME = "paddemy-backend"
COVERAGE_THRESHOLD = 80
CONDITION_COVERAGE_THRESHOLD = 60

# === FUNCIONES AUXILIARES ===
def sonar_api(path):
    return f"{SONAR_URL}/api/{path}"

def wait_for_sonar():
    print("⏳ Esperando a que SonarQube esté disponible...")
    for _ in range(30):
        try:
            r = requests.get(sonar_api("system/status"))
            if r.status_code == 200 and r.json().get("status") == "UP":
                print("✅ SonarQube está listo.")
                return
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
    print("❌ SonarQube no responde en http://localhost:9000")
    sys.exit(1)

def change_admin_password():
    print("🔍 Comprobando contraseña del admin...")
    resp = requests.get(sonar_api("authentication/validate"), auth=("admin", OLD_ADMIN_PASSWORD))
    if resp.status_code == 200 and resp.json().get("valid"):
        print("🔑 Cambiando contraseña del admin...")
        change_resp = requests.post(
            sonar_api("users/change_password"),
            auth=("admin", OLD_ADMIN_PASSWORD),
            data={"login": "admin", "previousPassword": OLD_ADMIN_PASSWORD, "password": NEW_ADMIN_PASSWORD},
        )
        if change_resp.status_code == 204:
            print("✅ Contraseña del admin cambiada correctamente.")
        else:
            print(f"⚠️ Error cambiando la contraseña: {change_resp.status_code} {change_resp.text}")
    else:
        print("✅ La contraseña del admin ya está cambiada o no es la predeterminada.")

def create_token():
    print("🔧 Creando token para Maven...")
    list_resp = requests.get(sonar_api("user_tokens/search"), auth=("admin", NEW_ADMIN_PASSWORD))
    if list_resp.status_code == 200:
        for t in list_resp.json().get("userTokens", []):
            if t["name"] == TOKEN_NAME:
                print("🗑️ Borrando token antiguo...")
                requests.post(
                    sonar_api("user_tokens/revoke"),
                    auth=("admin", NEW_ADMIN_PASSWORD),
                    data={"name": TOKEN_NAME},
                )

    token_resp = requests.post(
        sonar_api("user_tokens/generate"),
        auth=("admin", NEW_ADMIN_PASSWORD),
        data={"name": TOKEN_NAME},
    )

    if token_resp.status_code == 200:
        token = token_resp.json().get("token")
        print(f"✅ Token generado correctamente:\n\n{token}\n")
        return token
    else:
        print(f"⚠️ Error creando token: {token_resp.status_code} {token_resp.text}")
        return None

def ensure_project_exists(project_key, project_name):
    print(f"🔍 Comprobando si existe el proyecto '{project_key}'...")
    resp = requests.get(sonar_api(f"projects/search?projects={project_key}"), auth=("admin", NEW_ADMIN_PASSWORD))
    if resp.status_code == 200 and resp.json().get("components"):
        print("✅ El proyecto ya existe.")
        return True

    print("🆕 Creando proyecto en SonarQube...")
    create_resp = requests.post(
        sonar_api("projects/create"),
        auth=("admin", NEW_ADMIN_PASSWORD),
        data={"project": project_key, "name": project_name},
    )
    if create_resp.status_code == 200:
        print("✅ Proyecto creado correctamente.")
        return True
    else:
        print(f"⚠️ Error creando el proyecto: {create_resp.status_code} {create_resp.text}")
        return False

# === QUALITY GATE (Las condiciones de aprobación, es decir, qué condiciones debe cumplir el código para considerarse aceptable) ===
def create_quality_gate():
    print("🧱 Creando Quality Gate personalizado...")
    gates = requests.get(sonar_api("qualitygates/list"), auth=("admin", NEW_ADMIN_PASSWORD))
    if gates.status_code == 200:
        for g in gates.json().get("qualitygates", []):
            if g["name"] == QUALITY_GATE_NAME:
                print(f"✅ Quality Gate '{QUALITY_GATE_NAME}' ya existe.")
                return g

    gate_resp = requests.post(
        sonar_api("qualitygates/create"),
        auth=("admin", NEW_ADMIN_PASSWORD),
        data={"name": QUALITY_GATE_NAME},
    )
    if gate_resp.status_code != 200:
        print(f"⚠️ Error creando el Quality Gate: {gate_resp.status_code} {gate_resp.text}")
        return None

    requests.post(
        sonar_api("qualitygates/create_condition"),
        auth=("admin", NEW_ADMIN_PASSWORD),
        data={"gateName": QUALITY_GATE_NAME, "metric": "coverage", "op": "LT", "error": COVERAGE_THRESHOLD},
    )
    requests.post(
        sonar_api("qualitygates/create_condition"),
        auth=("admin", NEW_ADMIN_PASSWORD),
        data={"gateName": QUALITY_GATE_NAME, "metric": "branch_coverage", "op": "LT", "error": CONDITION_COVERAGE_THRESHOLD},
    )

    print(f"✅ Quality Gate '{QUALITY_GATE_NAME}' creado con éxito.")
    return QUALITY_GATE_NAME

# === QUALITY PROFILE (Las reglas de análisis, es decir, qué reglas se aplican durante el análisis) ===
def assign_quality_gate(project_key, gate_name):
    print(f"🔗 Asignando Quality Gate '{gate_name}' al proyecto '{project_key}'...")
    assign_resp = requests.post(
        sonar_api("qualitygates/select"),
        auth=("admin", NEW_ADMIN_PASSWORD),
        data={"projectKey": project_key, "gateName": gate_name},
    )
    if assign_resp.status_code == 204:
        print("✅ Quality Gate asignado correctamente.")
    else:
        print(f"⚠️ Error asignando el Quality Gate: {assign_resp.status_code} {assign_resp.text}")

def duplicate_quality_profile():
    print("🧬 Creando perfil de calidad personalizado...")
    profiles = requests.get(sonar_api("qualityprofiles/search?language=java"), auth=("admin", NEW_ADMIN_PASSWORD))
    if profiles.status_code != 200:
        print(f"⚠️ No se pudo obtener la lista de perfiles: {profiles.status_code}")
        return None

    sonar_way = next((p for p in profiles.json().get("profiles", []) if p["name"] == "Sonar way"), None)
    if not sonar_way:
        print("❌ No se encontró el perfil 'Sonar way' para Java.")
        return None

    for p in profiles.json().get("profiles", []):
        if p["name"] == QUALITY_PROFILE_NAME:
            print(f"✅ El perfil '{QUALITY_PROFILE_NAME}' ya existe.")
            return QUALITY_PROFILE_NAME

    dup_resp = requests.post(
        sonar_api("qualityprofiles/copy"),
        auth=("admin", NEW_ADMIN_PASSWORD),
        data={"fromKey": sonar_way["key"], "toName": QUALITY_PROFILE_NAME},
    )
    if dup_resp.status_code == 200:
        print(f"✅ Perfil de calidad '{QUALITY_PROFILE_NAME}' creado.")
        return QUALITY_PROFILE_NAME
    else:
        print(f"⚠️ Error creando perfil de calidad: {dup_resp.status_code} {dup_resp.text}")
        return None

def assign_quality_profile(project_key, profile_name):
    print(f"🔗 Asignando perfil de calidad '{profile_name}' al proyecto '{project_key}'...")
    assign_resp = requests.post(
        sonar_api("qualityprofiles/add_project"),
        auth=("admin", NEW_ADMIN_PASSWORD),
        data={"language": "java", "project": project_key, "qualityProfile": profile_name},
    )
    if assign_resp.status_code == 204:
        print("✅ Perfil de calidad asignado correctamente.")
    else:
        print(f"⚠️ Error asignando el perfil: {assign_resp.status_code} {assign_resp.text}")

# === MAIN ===
if __name__ == "__main__":
    wait_for_sonar()
    change_admin_password()
    token = create_token()
    ensure_project_exists(PROJECT_KEY, PROJECT_NAME)
    gate = create_quality_gate()
    profile = duplicate_quality_profile()
    if gate:
        assign_quality_gate(PROJECT_KEY, QUALITY_GATE_NAME)
    if profile:
        assign_quality_profile(PROJECT_KEY, QUALITY_PROFILE_NAME)

    print("\n🚀 Todo listo. Ejecuta el siguiente comando Maven para analizar el proyecto:\n")
    print(f"mvn clean verify sonar:sonar "
          f"-Dsonar.token={token} "
          f"-Dsonar.host.url={SONAR_URL} "
          f"-Dsonar.projectKey={PROJECT_KEY}")
