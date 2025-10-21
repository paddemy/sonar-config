# Guía de configuración local de SonarQube

Este directorio contiene todo lo necesario para **levantar SonarQube en local** con Docker y analizar proyectos **paddemy-backend** con Maven.

---

## Contenido

```
sonar-config/
│
├── docker-compose.yml        # Levanta SonarQube y su base de datos PostgreSQL
├── init_sonar.py             # Script de inicialización automática de SonarQube
└── README.md                 # Esta guía
```

---

## 🧰 0️⃣ Prerrequisitos

Antes de comenzar, asegúrate de tener instaladas las siguientes herramientas en tu entorno local:

| Herramienta        | Versión recomendada | Comando para comprobar                                |
| ------------------ | ------------------- | ----------------------------------------------------- |
| **Docker**         | ≥ 24.x              | `docker --version`                                    |
| **Docker Compose** | ≥ 2.x               | `docker compose version` o `docker-compose --version` |
| **Python 3**       | ≥ 3.8               | `python3 --version`                                   |
| **Maven**          | ≥ 3.8               | `mvn -v`                                              |
| **Java (JDK)**     | ≥ 21                | `java -version`                                       |

> 💡 Si `python` no está vinculado a `python3`, puedes crear un alias temporal:
> ```bash
> alias python=python3
> ```
> o hacerlo permanente con:
> ```bash
> echo "alias python=python3" >> ~/.zshrc && source ~/.zshrc
> ```

#### 📦 Módulos de Python requeridos

El script `init_sonar.py` requiere la librería `requests` para comunicarse con la API de SonarQube.

Instálala ejecutando:

```bash
pip install requests
```

Puedes verificar la instalación con:

```bash
python3 -m pip show requests
```

---

## 1️⃣ Levantar SonarQube en local

Desde la raíz del proyecto o desde `sonar-config/`, ejecuta:

```bash
docker-compose up -d
```

Esto levantará:

- **SonarQube** en [http://localhost:9000](http://localhost:9000)
- **PostgreSQL** como base de datos interna de Sonar

> 💡 Consejo: la primera vez puede tardar un poco (30–60s) en inicializarse.

---

## 2️⃣ Inicializar SonarQube con el script

Ejecuta el script con Python 3:

```bash
python3 init_sonar.py
```

> ⚠️ Asegúrate de que SonarQube ya está completamente levantado antes de ejecutar el script.

¿Qué ha hecho el script?:

- Cambia la contraseña por defecto de `admin` → `$4adminP@ssw0rd` (si aún no estaba cambiada)  
- Crea un token de acceso para Maven  
- Crea el proyecto `paddemy_backend_key` (si no existía)  
- Crea un **Quality Gate personalizado** (“Paddemy Local Quality Gate”)  
- Crea un **Quality Profile personalizado** (“Paddemy Local Java Rules”)  
- Asigna ese Quality Gate al proyecto  
- Asigna ese Quality Profile al proyecto  
- Muestra el comando Maven exacto para el análisis

---

## 3️⃣ Ejecutar el análisis con Maven

Cuando el script termine, mostrará un comando similar a este:

```bash
mvn clean verify sonar:sonar \
  -Dsonar.token=squ_d50a753a8c44c633ded5fc0711929a52f3e4b3df \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.projectKey=paddemy_backend_key
```

Ejecuta ese comando desde la raíz del proyecto que quieres analizar.

---

## 4️⃣ Revisar resultados

Una vez finalizado el análisis, abre [http://localhost:9000](http://localhost:9000):

- Usuario: `admin`
- Contraseña: `$4adminP@ssw0rd`

Busca el proyecto paddemy-backend (el único 😊) y revisa:
- Bugs
- Vulnerabilidades
- Code Smells
- Test Coverage
- Cumplimiento del Quality Gate

---

## 5️⃣ Limpiar completamente los datos de SonarQube

Si quieres **reiniciar** SonarQube desde cero (borrar todos los proyectos, reglas y configuraciones):

```bash
docker-compose down -v --rmi all
```

Esto eliminará los contenedores, volúmenes y datos persistentes de la base de datos.

---

## 🧠 Notas para desarrolladores

- **Quality Profile:** define las reglas de análisis (qué se detecta).
- **Quality Gate:** define las condiciones mínimas para aprobar (por ejemplo, cobertura ≥ 90%).
- Puedes personalizar las reglas y Quality Gates desde la interfaz web de SonarQube.
- Si necesitas un nuevo token, puedes generarlo manualmente en:  
  **Administration → Security → My Account → Security → Generate Tokens**

---

## 🧩 Referencias

- [SonarQube Documentation](https://docs.sonarsource.com/sonarqube/latest/)
- [Sonar Maven Plugin](https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner-for-maven/)
- [Docker Hub: sonarqube](https://hub.docker.com/_/sonarqube)

---

**💜 Proyecto Paddemy — Configuración local de calidad de código**
