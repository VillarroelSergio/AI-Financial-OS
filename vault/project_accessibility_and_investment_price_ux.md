---
name: project_accessibility_and_investment_price_ux
description: El tamaño de texto es una preferencia persistente y la actualización manual distingue el NAV de los fondos.
metadata:
  type: project
---

La aplicación ofrece en Ajustes cuatro tamaños de texto: compacto, normal, grande y muy grande. La preferencia se conserva localmente para aplicarse antes del primer render y se guarda también como `app.font_scale` en los ajustes de la aplicación. La escala base se elevó para que captions y textos auxiliares sean legibles por defecto.

Al actualizar precios sin proveedor automático, los fondos solicitan explícitamente el valor liquidativo (NAV) por participación. El diálogo muestra el número de participaciones y una estimación del valor total resultante; para el resto de activos solicita la cotización por unidad. No se debe pedir el importe total de la posición.

El Balance General es ahora solo una vista de activos, pasivos, patrimonio y evolución. El cierre mensual asistido y sus acciones se retiraron de la interfaz por no aportar valor al flujo de usuario.

**Por qué:** mejorar la legibilidad y evitar que el usuario confunda el NAV de un fondo con el valor total invertido.
**Cómo aplicarlo:** cualquier nuevo texto auxiliar debe respetar la escala tipográfica global; los futuros flujos de valoración de fondos deben mantener la distinción entre NAV por participación y valor de la posición.

**Validación (2026-07-16):** la captura dirigida de `/settings` confirma que la pantalla monta y muestra el selector. Se restauró el `ToastProvider` en `App`, que faltaba y provocaba que `useToast` desmontase la pantalla. La E2E aislada informa 26 PASS, 7 BLOCKED conocidos, cero errores de consola y cero HTTP 5xx; los contratos de calidad UI y el build del desktop pasan.

**Corrección posterior (2026-07-16):** los aliases tipográficos de Tailwind mantenían píxeles fijos y evitaban que la escala llegase a la mayor parte de la aplicación. Todos los tamaños compartidos y los tamaños arbitrarios usados pasan a depender de `--font-scale`. Se conservan las animaciones existentes y se amplía el feedback táctil a botones heredados y tarjetas, respetando `prefers-reduced-motion`.

**Corrección de contador (2026-07-16):** `CountUp` actualizaba su valor anterior antes de terminar la animación. En modo estricto de React el primer efecto se cancela y el segundo quedaba sin distancia que recorrer. El valor anterior se guarda ahora al completar la transición, por lo que el patrimonio vuelve a contar desde el importe previo o desde cero al montar.

**Microinteracciones transversales (2026-07-16):** las superficies `premium-card`, `mercury-panel`, `bg-surface-card` y las tarjetas elevadas grandes comparten elevación sutil al pasar el puntero. Así el feedback no queda limitado al Resumen. Con `prefers-reduced-motion` no se desplazan.

Las mismas superficies comparten también una entrada de 360 ms desde 8 px por debajo, con opacidad y escala mínimas y un escalonado máximo de 120 ms. Los KPI de Resumen conservan su animación Framer Motion para evitar duplicarla. Las barras de progreso y asignación se revelan desde el origen izquierdo al montar o al cambiar de filtro. En movimiento reducido, estas entradas se desactivan.

**Chrome minimalista (2026-07-16):** en escritorio se retira la barra superior que repetía el nombre de la sección y su divisor horizontal. Las pestañas de Finanzas dejan de dibujar un segundo divisor, pero conservan el indicador azul de selección. El copiloto contextual pasa a ser un control flotante discreto para mantener la funcionalidad sin recuperar una barra vacía. La cabecera móvil se conserva porque aporta contexto y navegación en pantallas estrechas.

---
**Relacionadas:** [[project_investments_module]] · [[20_REDESIGN_ATELIER]] · [[GLOSARIO]]

Tags: #project #accesibilidad #inversiones #ux
