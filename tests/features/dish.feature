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
