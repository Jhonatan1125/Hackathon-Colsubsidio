SoterIA & Sistema Crediticio Hiperpersonalizado (Hackathon 30X)
SoterIA (del griego Soteria: confianza/salvación, e IA: Inteligencia Artificial) es una solución integral orientada a la venta consultiva automatizada y la colocación de productos financieros. Este repositorio documenta la arquitectura de dos proyectos interconectados que centralizan la atención al cliente, la perfilación de usuarios y la generación de ofertas hiperpersonalizadas a través de múltiples canales.

1. NOMBRE DEL PROYECTO
SoterIA & Sistema Crediticio Hiperpersonalizado
Plataforma unificada de seguros y servicios financieros impulsada por IA Generativa y Machine Learning. Proyecto destacado - Hackathon 30X.

2. EL PROBLEMA
Las entidades financieras y aseguradoras enfrentan un cuello de botella en sus embudos de conversión debido a la dependencia de procesos manuales y agentes humanos.

En Seguros: La venta cruzada y consultiva de pólizas (carros, motos, patinetas/bicicletas y mascotas) carece de escalabilidad y no opera 24/7, perdiendo prospectos interesados.

En Créditos: Las campañas de colocación de créditos suelen ser genéricas. No analizan a profundidad la capacidad o necesidad del cliente, lo que resulta en bajas tasas de conversión y fricción en los canales de mensajería directa como WhatsApp.

3. SOLUCIÓN Y ARQUITECTURA
Desarrollamos una arquitectura de dos módulos integrados de alta tecnología, respaldados por bases de datos en Azure y un ecosistema escalable dividido en múltiples repositorios:

Módulo 1: SoterIA (Agente Conversacional en Copilot Studio)

Interfaz principal orientada a la atención y venta consultiva.

Gestiona dinámicamente flujos especializados para la venta de seguros de: Carros, Motos, Patinetas/Bicicletas y Mascotas.

Aplica metodologías de perfilamiento en tiempo real para guiar al usuario desde la curiosidad hasta la intención de compra.

Módulo 2: Motor de Créditos Hiperpersonalizados (ML + LLM Local + Frontend)

Repositorio Core/Backend (Hackathon-30X)

Repositorio Frontend

Se accede desde una temática específica en Copilot Studio, la cual dispara un flujo de Power Automate para consumir la API del motor de créditos.

Pipeline de Procesamiento:

Ingesta: Carga de archivos CSV con las cédulas de los usuarios registrados mediante una interfaz Frontend dedicada.

Análisis Predictivo: Extracción de variables clave y evaluación mediante un modelo de Machine Learning que genera predicciones sobre la viabilidad y tipo de crédito.

Hiperpersonalización: Envío de las predicciones a un LLM Local, el cual redacta de manera autónoma un mensaje único basado en el perfil exacto del cliente.

Distribución: Enrutamiento a través de un wrapper personalizado con validaciones específicas para la entrega exitosa del mensaje vía WhatsApp.

4. COMPETENCIA
Chatbots tradicionales basados en reglas: No tienen la capacidad de realizar perfilamiento semántico ni ventas consultivas dinámicas.

Call Centers y fuerza de ventas humana: Limitados por horarios laborales, altos costos operativos y sesgos en la oferta de productos.

Sistemas de CRM con envíos masivos genéricos: Carecen de la inteligencia de un LLM local para redactar mensajes uno-a-uno, lo que los condena a bajas tasas de apertura en canales directos.

5. EQUIPO
Un equipo multidisciplinario enfocado en la ingeniería de sistemas, arquitectura cloud y desarrollo de interfaces:

Mateo Sotelo - Arquitectura Cloud (Azure), Data Engineering y Desarrollo en ecosistema Microsoft (Copilot Studio & Power Automate).

Desarrollo Full-Stack / ML (D4V1D16) - Integración de modelos predictivos, lógica del motor de créditos y desarrollo de la interfaz Frontend para la gestión de datos.

6. DÓNDE ESTÁN Y DÓNDE QUIEREN IR
Dónde estamos:
Contamos con la infraestructura cloud desplegada (Azure DBs y el tenant de Copilot Studio). El ecosistema de SoterIA es capaz de orquestar la venta de los 4 tipos de seguros. A su vez, el pipeline de predicción de créditos (Frontend -> CSV -> ML -> LLM Local -> Wrapper de WhatsApp) fue construido y validado exitosamente durante la Hackathon 30X.

Dónde queremos ir:
Buscamos escalar el despliegue para soportar un mayor volumen de transacciones concurrentes, certificar la integración oficial de la API de WhatsApp Business para el wrapper, y consolidar el modelo de Machine Learning con datos de retroalimentación en tiempo real para aumentar continuamente la precisión de la hiperpersonalización.

7. QUÉ ES LO QUE NECESITAN
Capacidad de Cómputo / Escalabilidad Cloud: Recursos adicionales en Azure para soportar el LLM local y los picos de procesamiento del modelo de Machine Learning al ingerir lotes grandes de CSV desde el Frontend.

Aprobaciones de API Oficiales: Aprobación de plantillas y límites de mensajería en WhatsApp Business API para evitar bloqueos del wrapper.

Feedback de Datos Históricos: Acceso a mayores volúmenes de datos transaccionales para afinar las redes neuronales y algoritmos de predicción crediticia.
