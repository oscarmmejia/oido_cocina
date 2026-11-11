Feature: Gestión de colecciones de menú
  Como jefe de cocina
  Quiero crear, editar y borrar colecciones de menús con tipo y vigencia
  Para agrupar menús diarios, de temporada o festivos sin romper el histórico

  Scenario: Crear una colección con datos válidos
    Given que existe un restaurante
    When creo una colección llamada "Navidad 2026" de tipo "fixed"
    Then la colección se crea correctamente
    And queda activa y asociada a ese restaurante

  Scenario: No permitir nombres duplicados en el mismo restaurante
    Given que el restaurante 1 ya tiene la colección "Verano"
    When intento crear otra colección llamada "Verano" en ese restaurante
    Then la operación se rechaza con un conflicto
    And no se guarda ningún dato

  Scenario: Rechazar una vigencia incoherente
    Given que existe un restaurante
    When creo una colección con valid_from "2026-12-31" y valid_to "2026-01-01"
    Then la operación se rechaza con un error 422
    And no se guarda ningún dato

  Scenario: Editar el nombre y la vigencia de una colección
    Given que existe una colección guardada
    When le asigno el nombre "Menús de temporada" y la vigencia desde "2026-11-01"
    Then la colección se actualiza correctamente

  Scenario: Borrar una colección sin menús
    Given que existe una colección sin menús
    When se borra la colección
    Then la colección desaparece de la base de datos

  Scenario: Rechazar el borrado sin permiso menu:update
    Given que existe una colección sin menús
    When se intenta borrar la colección sin permiso
    Then la operación se rechaza con un error 403
    And la colección se conserva

  Scenario: No borrar una colección con menús
    Given que existe una colección con al menos un menú
    When se intenta borrar la colección
    Then la operación se rechaza con un error 409
    And la colección sigue existiendo

  Scenario: No borrar una colección de otro restaurante
    Given que la colección 5 pertenece al restaurante 2
    When el restaurante 1 intenta borrar esa colección
    Then la operación se rechaza con un error 404
    And la colección se conserva

  Scenario: No exponer los menús de una colección inactiva
    Given que existe una colección inactiva con menús
    When se consulta la carta pública del restaurante
    Then sus menús no aparecen

  Scenario: No exponer los menús de una colección vencida
    Given que existe una colección con valid_to en el pasado y con menús
    When se consulta la carta pública del restaurante
    Then sus menús no aparecen