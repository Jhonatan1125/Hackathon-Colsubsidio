<div align="center">

# 🤖 SoterIA & Sistema Crediticio Hiperpersonalizado

> *Del griego **Soteria** (confianza/salvación) + **IA** (Inteligencia Artificial)*

**Plataforma unificada de seguros y servicios financieros impulsada por IA Generativa y Machine Learning.**
Proyecto destacado originado en la **Hackathon 30X** 🏆

[![Live Demo](https://img.shields.io/badge/🌐_Demo_en_Vivo-Probar_SoterIA-4A90E2?style=for-the-badge)](https://jhonatan1125.github.io/colsubsidio-seguros/)
[![Azure](https://img.shields.io/badge/Cloud-Microsoft_Azure-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white)](https://azure.microsoft.com)
[![Copilot Studio](https://img.shields.io/badge/Microsoft-Copilot_Studio-7B2FBE?style=for-the-badge&logo=microsoft&logoColor=white)](https://copilotstudio.microsoft.com)
[![Power Automate](https://img.shields.io/badge/Power-Automate-0066FF?style=for-the-badge&logo=powerautomate&logoColor=white)](https://powerautomate.microsoft.com)

---

*Una solución integral orientada a la **venta consultiva automatizada** y la **colocación de productos financieros**, centralizando la atención al cliente, la perfilación de usuarios y la generación de ofertas hiperpersonalizadas a través de múltiples canales.*

</div>

---

## 📋 Tabla de Contenidos

- [⚠️ El Problema](#️-el-problema)
- [💡 Solución y Arquitectura](#-solución-y-arquitectura)
- [🥊 Ventaja Competitiva](#-ventaja-competitiva)
- [👥 El Equipo](#-el-equipo)
- [🚀 Hoja de Ruta](#-hoja-de-ruta)
- [🛠️ Qué Necesitamos](#️-qué-necesitamos)
- [📱 Cómo Usar la Aplicación](#-cómo-usar-la-aplicación)

---

## ⚠️ El Problema

Las entidades financieras y aseguradoras enfrentan un **cuello de botella crítico** en sus embudos de conversión por la dependencia de procesos manuales y agentes humanos:

<table>
<tr>
<td width="50%" valign="top">

### 📉 En Seguros

La venta cruzada y consultiva de pólizas *(carros, motos, patinetas/bicicletas y mascotas)* carece de escalabilidad.

Al no operar **24/7**, se pierde el *momentum* del cliente y la oportunidad de cierre.

</td>
<td width="50%" valign="top">

### 📉 En Créditos

Las campañas de colocación suelen ser **invasivas y genéricas** (spam).

No analizan la capacidad o necesidad real del cliente, resultando en **altísimas tasas de rechazo** y fricción en canales como WhatsApp.

</td>
</tr>
</table>

---

## 💡 Solución y Arquitectura

Arquitectura de **dos módulos integrados**, respaldados por bases de datos en **Microsoft Azure** y un ecosistema escalable dividido en microservicios:

### 🛡️ Módulo 1 — SoterIA *(Agente Conversacional en Copilot Studio)*

Interfaz principal orientada a la atención al cliente y **venta consultiva automatizada**.

| Capacidad | Descripción |
|---|---|
| 🚗 **Seguros de Vehículos** | Carros, Motos, Patinetas y Bicicletas |
| 🐾 **Seguros de Mascotas** | Cobertura personalizada para tus animales |
| 🧠 **Perfilamiento SPIN** | Metodología de ventas aplicada en tiempo real |
| ⏰ **Disponibilidad 24/7** | Sin dependencia de agentes humanos |

> Aplica metodologías de **Spin Selling** en tiempo real para guiar al usuario desde el interés inicial hasta la **intención de compra**.

---

### 💳 Módulo 2 — Motor de Créditos Hiperpersonalizados *(ML + LLM Local + Frontend)*

> 🔗 **Repositorios asociados:** [Backend / Core API (Hackathon-30X)](https://github.com) · [Frontend Interface](https://github.com)

Este módulo se activa desde Copilot Studio, disparando un flujo de **Power Automate** para consumir la API del motor de créditos.

#### ⚙️ Pipeline de Procesamiento

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌────────────────────┐
│   Frontend  │────▶│  Machine Learning │────▶│   LLM Local     │────▶│  WhatsApp Wrapper  │
│  (CSV Load) │     │  (Análisis Pred.) │     │  (Redacción 1:1)│     │  (Entrega Final)   │
└─────────────┘     └──────────────────┘     └─────────────────┘     └────────────────────┘
```

| Fase | Componente | Descripción |
|---|---|---|
| **1️⃣ Ingesta** | Frontend | Carga masiva de `.csv` con cédulas de usuarios registrados |
| **2️⃣ Análisis** | Machine Learning | Evaluación de viabilidad, monto y tipo de crédito ideal por perfil |
| **3️⃣ Personalización** | LLM Local | Redacción autónoma de mensajes persuasivos y únicos por cliente |
| **4️⃣ Distribución** | WhatsApp Wrapper | Enrutamiento con reglas de validación para entrega exitosa |

---

## 🥊 Ventaja Competitiva

| Alternativa Actual | Limitación | ✅ Nuestra Solución |
|---|---|---|
| 🤖 Chatbots por Reglas | Sin perfilamiento semántico ni memoria contextual | Venta consultiva dinámica con IA |
| 📞 Call Centers Tradicionales | Horarios limitados y altos costos operativos | Operación 24/7 sin fricción humana |
| 📧 CRMs con Envíos Masivos | Mensajes genéricos, spam, bajas tasas de apertura | Mensajes 1:1 redactados por LLM local |

---

## 👥 El Equipo

Un equipo multidisciplinario experto en **Inteligencia Artificial**, **Arquitectura Cloud** y **Desarrollo de Interfaces**:

<table>
<tr>
<td width="33%" align="center" valign="top">

### 👨‍💻 David Jimenez
**Full-Stack Developer & ML Integrator**

Integración de modelos predictivos, lógica central del motor de créditos y desarrollo del Frontend para la gestión de datos.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/sjimenez16/)

</td>
<td width="33%" align="center" valign="top">

### 📊 Dautmer Martinez
**Data Analyst & ML Engineer**

EDA, extracción de características, entrenamiento y optimización de algoritmos predictivos para máxima precisión financiera.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/dautmer-contreras/)

</td>
<td width="33%" align="center" valign="top">

### 🤖 Jhonatan Gonzalez
**Copilot Maker & Agents Architect**

Construcción de flujos conversacionales, prompt engineering avanzado y orquestación de SoterIA en el ecosistema Microsoft.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/jhonatang25/)

</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">

### ☁️ Mateo Sotelo
**Cloud Architect & Data Engineer**

Infraestructura en Azure, despliegue de bases de datos y orquestación de servicios mediante Power Automate.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/mateo-sotelo-709852288/)

</td>
<td width="33%" align="center" valign="top">

### 🧪 Jorge Medina
**QA Tester & Copilot Trainer**

Pruebas de estrés, validación de flujos lógicos y entrenamiento continuo del agente para una experiencia de usuario perfecta.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/jorge-medina-rincon/)

</td>
<td width="33%" align="center" valign="top"></td>
</tr>
</table>

---

## 🚀 Hoja de Ruta

### 📍 Dónde Estamos Hoy

- ✅ Infraestructura cloud desplegada (Azure DBs + Tenant de Copilot Studio)
- ✅ SoterIA capaz de orquestar perfilación y venta de **4 tipos de seguros**
- ✅ Pipeline completo construido y validado: `Frontend → CSV → ML → LLM Local → WhatsApp Wrapper`

### 🎯 Hacia Dónde Vamos

- 📈 **Escalabilidad** — Soporte para mayor volumen de transacciones concurrentes
- 📲 **WhatsApp Business API** — Certificación e integración oficial del wrapper
- 🔄 **Feedback Loop** — Refinamiento del modelo ML con datos en tiempo real para mayor asertividad financiera

---

## 🛠️ Qué Necesitamos

Para escalar el proyecto a nivel corporativo masivo, requerimos:

| Recurso | Detalle |
|---|---|
| ⚡ **Cloud Scaling** | Créditos y recursos adicionales en Azure para inferencia del LLM local y picos de procesamiento ML |
| 📲 **WhatsApp API Oficial** | Verificación de negocio, aprobación de plantillas HSM y aumento de límites de mensajería |
| 📊 **Datos Históricos** | Acceso a mayores volúmenes de datos transaccionales reales para refinar las redes neuronales crediticias |

---

## 📱 Cómo Usar la Aplicación

Sigue estos pasos para interactuar con **SoterIA** y explorar sus capacidades de primera mano:

**① Accede a la plataforma**

```
https://jhonatan1125.github.io/colsubsidio-seguros/
```

**② Inicia la conversación**

Dirígete a la **esquina inferior derecha** y selecciona el botón flotante de chat *(ícono azul de mensaje)*.

**③ Acepta los términos**

Se desplegará la ventana del **Asistente Colsubsidio (SoterIA)**. Acepta los términos y condiciones para habilitar el perfilamiento inteligente.

**④ Explora los servicios disponibles**

| Servicio | Descripción |
|---|---|
| 🚗 **Seguros Carro / Moto** | Todo Riesgo, cobertura completa |
| 🚲 **Patinetas y Bicicletas** | Seguros para movilidad alternativa |
| 🐶 **Mascotas** | Protección para tu familia peludita |
| 💳 **Créditos** | Consulta y perfilamiento hiperpersonalizado |

---

<div align="center">

**Construido con ❤️ durante la Hackathon 30X**

[![Probar Demo](https://img.shields.io/badge/🚀_Probar_Demo-Ahora-28a745?style=for-the-badge)](https://jhonatan1125.github.io/colsubsidio-seguros/)

</div>
