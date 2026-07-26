🤖 SoterIA & Sistema Crediticio Hiperpersonalizado
SoterIA (del griego Soteria: confianza/salvación, e IA: Inteligencia Artificial) es una solución integral orientada a la venta consultiva automatizada y la colocación de productos financieros. Este repositorio documenta la arquitectura de dos proyectos interconectados que centralizan la atención al cliente, la perfilación de usuarios y la generación de ofertas hiperpersonalizadas a través de múltiples canales.

📌 1. NOMBRE DEL PROYECTO
SoterIA & Sistema Crediticio Hiperpersonalizado

Plataforma unificada de seguros y servicios financieros impulsada por IA Generativa y Machine Learning. Proyecto destacado originado en la Hackathon 30X.

⚠️ 2. EL PROBLEMA
Las entidades financieras y aseguradoras enfrentan un cuello de botella crítico en sus embudos de conversión debido a la dependencia de procesos manuales y agentes humanos:

📉 En Seguros: La venta cruzada y consultiva de pólizas (carros, motos, patinetas/bicicletas y mascotas) carece de escalabilidad. Al no operar 24/7, se pierde el momentum del cliente y la oportunidad de cierre.

📉 En Créditos: Las campañas de colocación de créditos suelen ser invasivas y genéricas (spam). No analizan a profundidad la capacidad o necesidad real del cliente, lo que resulta en altísimas tasas de rechazo y fricción en los canales de mensajería directa como WhatsApp.

💡 3. SOLUCIÓN Y ARQUITECTURA
Desarrollamos una arquitectura de dos módulos integrados de alta tecnología, respaldados por bases de datos en Microsoft Azure y un ecosistema escalable dividido en microservicios/repositorios:

🛡️ Módulo 1: SoterIA (Agente Conversacional en Copilot Studio)
Interfaz principal orientada a la atención al cliente y venta consultiva automatizada.

Gestiona dinámicamente flujos especializados para la venta de seguros de: Carros | Motos | Patinetas/Bicicletas | Mascotas.

Aplica metodologías de perfilamiento (Spin Selling) en tiempo real para guiar al usuario desde el interés inicial hasta la intención de compra.

💳 Módulo 2: Motor de Créditos Hiperpersonalizados (ML + LLM Local + Frontend)
🔗 Repositorios asociados:

Backend / Core API (Hackathon-30X)

Frontend Interface

Este módulo se activa desde Copilot Studio, disparando un flujo de Power Automate para consumir la API del motor de créditos.

Flujo de Procesamiento (Pipeline):

Ingesta (Frontend): Carga masiva de archivos .csv con las cédulas de los usuarios registrados.

Análisis Predictivo (Machine Learning): Extracción de variables clave y evaluación matemática para generar predicciones sobre la viabilidad, monto y tipo de crédito ideal para cada perfil.

Hiperpersonalización (LLM Local): Envío de las predicciones a un Modelo de Lenguaje Grande (LLM) alojado localmente, el cual redacta de manera autónoma un mensaje persuasivo y único, ajustado al perfil exacto del cliente.

Distribución Omnicanal: Enrutamiento a través de un wrapper personalizado con reglas de validación estrictas para garantizar la entrega exitosa del mensaje vía WhatsApp.

🥊 4. COMPETENCIA
Nuestra solución supera las alternativas actuales del mercado por las siguientes razones:

❌ Chatbots basados en reglas: No tienen la capacidad de realizar perfilamiento semántico, carecen de memoria contextual y no logran ventas consultivas dinámicas.

❌ Call Centers tradicionales: Limitados por horarios laborales, altos costos operativos y sesgos en la oferta de productos.

❌ CRMs con envíos masivos: Carecen de la inteligencia de un LLM local para redactar mensajes uno-a-uno, condenándolos a bajas tasas de apertura y bloqueos por spam en WhatsApp.

👥 5. EQUIPO
Un equipo multidisciplinario experto en Inteligencia Artificial, Arquitectura Cloud y Desarrollo de Interfaces:

👨‍💻 David Jimenez | Full-Stack Developer & ML Integrator

Encargado de la integración de los modelos predictivos, lógica central del motor de créditos y desarrollo de la interfaz Frontend para la gestión de datos.

📊 Dautmer Martinez | Data Analyst & Machine Learning Engineer

Especialista en el análisis exploratorio de datos (EDA), extracción de características, entrenamiento y optimización de los algoritmos predictivos para asegurar la máxima precisión financiera.

🤖 Jhonatan Gonzalez | Copilot Maker & Agents Manipulator

Experto en la construcción de los flujos conversacionales, prompt engineering avanzado y orquestación del comportamiento de SoterIA en el ecosistema Microsoft.

☁️ Mateo Sotelo | Cloud Architect & Data Engineer

Responsable de la infraestructura en Azure, despliegue de bases de datos, y orquestación de la integración de servicios mediante Power Automate.

🧪 Jorge Medina | QA Tester & Copilot Trainer

Líder de aseguramiento de calidad. Encargado de las pruebas de estrés, validación de los flujos lógicos y entrenamiento continuo del agente para garantizar una experiencia de usuario perfecta.

🚀 6. DÓNDE ESTAMOS Y DÓNDE QUEREMOS IR
📍 Dónde estamos:
Contamos con la infraestructura cloud desplegada (Azure DBs y Tenant de Copilot Studio). El ecosistema de SoterIA es capaz de orquestar la perfilación y venta de los 4 tipos de seguros. A su vez, el pipeline del motor de créditos (Frontend -> CSV -> ML -> LLM Local -> Wrapper de WhatsApp) fue construido, conectado y validado exitosamente durante la Hackathon 30X.

🎯 Dónde queremos ir:
Buscamos escalar el despliegue para soportar un mayor volumen de transacciones concurrentes, lograr la certificación e integración oficial de la API de WhatsApp Business para nuestro wrapper, y consolidar el modelo de ML con datos de retroalimentación (feedback loop) en tiempo real para aumentar la asertividad financiera.

🛠️ 7. QUÉ ES LO QUE NECESITAMOS
Para escalar el proyecto a un nivel corporativo masivo, requerimos:

Capacidad de Cómputo (Cloud Scaling): Recursos adicionales y créditos en Azure para soportar la inferencia del LLM local y manejar los picos de procesamiento del ML al ingerir lotes masivos de datos desde el Frontend.

Aprobaciones Oficiales (WhatsApp API): Verificación de negocio, aprobación de plantillas HSM y aumento de límites de mensajería en la API oficial de WhatsApp para evitar bloqueos del wrapper.

Feedback de Datos Históricos: Acceso a mayores volúmenes de datos transaccionales reales para refinar las redes neuronales y algoritmos de predicción crediticia, disminuyendo el margen de error.

📱 8. CÓMO USAR LA APLICACIÓN (PASO A PASO)
Para interactuar con SoterIA y explorar de primera mano los flujos de atención y ventas, sigue estas instrucciones:

Accede a la plataforma web:
Ingresa a nuestro entorno de pruebas haciendo clic en el siguiente enlace:
https://jhonatan1125.github.io/colsubsidio-seguros/

Inicia la conversación:
Una vez en la página, dirígete a la esquina inferior derecha y selecciona el botón flotante de chat (icono azul de mensaje).

Interactúa con el asistente:
Se desplegará la ventana del Asistente Colsubsidio (SoterIA). Acepta los términos y condiciones iniciales para habilitar el perfilamiento inteligente.

Explora los servicios:
Utiliza el chat para realizar todo el flujo de consultas. El agente está capacitado para procesar solicitudes sobre:

🚗 Seguros de Carro o Moto (Todo Riesgo).

🚲 Seguros de Patinetas y Bicicletas.

🐶 Seguros para Mascotas.

💳 Información, consulta y perfilamiento de créditos hiperpersonalizados.
