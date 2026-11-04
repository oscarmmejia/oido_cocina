Feature: Gestión de categorías por restaurante

  Scenario: Crear una categoría correctamente
    Given que existe el restaurante con ID 1
    When se crea la categoría "Entrantes" para ese restaurante
    Then la categoría se guarda correctamente
    And queda asociada al restaurante 1

  Scenario: No permitir crear una categoría sin nombre
    Given que existe el restaurante con ID 1
    When se intenta crear una categoría sin nombre
    Then el sistema rechaza la operación

  Scenario: No permitir nombres duplicados en el mismo restaurante
    Given que el restaurante 1 ya tiene la categoría "Entrantes"
    When se intenta crear otra categoría llamada "Entrantes"
    Then el sistema devuelve un conflicto

  Scenario: No utilizar una categoría de otro restaurante
    Given que la categoría 1 pertenece al restaurante 1
    When el restaurante 2 intenta utilizar esa categoría
    Then el sistema rechaza la operación

  Scenario: No desactivar una categoría con platos activos
    Given que la categoría 1 tiene platos activos
    When se intenta desactivar la categoría
    Then el sistema devuelve un conflicto

  Scenario: Listar las categorías de un restaurante
    Given que el restaurante 1 tiene categorías registradas
    When se solicitan sus categorías
    Then el sistema devuelve únicamente las categorías del restaurante 1
