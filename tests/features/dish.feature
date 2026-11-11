Feature: Gestión de platos con alérgenos
  Como jefe de cocina
  Quiero crear, consultar y editar platos con sus alérgenos
  Para gestionar correctamente la carta del restaurante

  Scenario: Crear un plato con datos válidos y alérgenos
    Given que existe una categoría válida
    And existen los alérgenos gluten y huevo en el catálogo
    When creo un plato llamado "Tortilla" con precio 9.50
    And le asigno la categoría existente
    And le asigno los alérgenos gluten y huevo
    Then el plato se crea correctamente
    And queda asociado a dos alérgenos

  Scenario: Rechazar un plato sin nombre
    When intento crear un plato sin nombre
    Then la operación se rechaza con un error de validación
    And no se guarda ningún dato

  Scenario: Rechazar un plato sin categoría
    When intento crear un plato sin categoría
    Then la operación se rechaza con un error de validación
    And no se guarda ningún dato

  Scenario: Rechazar un precio negativo
    When intento crear un plato con precio -1
    Then la operación se rechaza con un error 422
    And no se guarda ningún dato

  Scenario: Rechazar un alérgeno que no existe
    Given que existe una categoría válida
    When intento crear un plato con un alérgeno que no está en el catálogo
    Then la operación se rechaza
    And no se guarda ningún dato

  Scenario: Consultar un plato sin depender de un menú
    Given que existe un plato guardado
    When consulto ese plato
    Then obtengo sus datos y sus alérgenos
    And no necesito que esté asociado a un menú

  Scenario: Evitar cambios parciales cuando falla una operación
    Given que existe un plato guardado
    When intento actualizarlo con un alérgeno que no existe
    Then la operación se rechaza
    And el plato conserva sus datos anteriores
    And conserva sus relaciones de alérgenos anteriores

  Scenario: Ocultar un plato no publicado en la carta pública
    Given que existe un plato activo pero no publicado
    When se consulta la carta pública
    Then el plato no aparece

  Scenario: Mostrar un plato no disponible como no disponible
    Given que existe un plato publicado y no disponible
    When se consulta la carta pública
    Then el plato aparece marcado como no disponible

  Scenario: Filtrar la carta pública por alérgeno
    Given un catálogo con platos con y sin gluten
    When se filtra por el alérgeno gluten
    Then solo aparecen los platos que lo contienen

  Scenario: Filtrar la carta pública por categoría y disponibilidad
    Given que existen platos de varias categorías y con distinta disponibilidad
    When se filtra por una categoría y por disponibilidad
    Then solo aparecen los platos que cumplen ambos filtros

  Scenario: Paginar la carta pública
    Given que existen cinco platos publicados
    When se consulta la segunda página con dos platos por página
    Then aparecen el tercer y el cuarto plato
    And el total indica cinco platos y tres páginas

  Scenario: Rechazar una paginación no válida
    When se consulta la carta pública con página 0
    Then la operación se rechaza con un error 422

  Scenario: Dar de baja un plato sin borrarlo
    Given que existe un plato activo
    When se desactiva el plato
    Then el plato se conserva en la base de datos
    And no aparece en la carta pública

  Scenario: Cambiar el estado de un plato
    Given que existe un plato no publicado
    When se cambia su estado a publicado
    Then el plato aparece en la carta pública

  Scenario: Rechazar un cambio de estado vacío
    Given que existe un plato guardado
    When se envía un cambio de estado sin ningún campo
    Then la operación se rechaza con un error 422
