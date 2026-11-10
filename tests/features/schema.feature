Feature: Esquema de datos compartido y seeders
  Como desarrollador
  Quiero disponer de un esquema completo, versionado y sembrado
  Para implementar historias funcionales en paralelo

  Scenario: Base vacía
    Given un entorno sin base de datos
    When se ejecutan las migraciones y los seeders
    Then el esquema y los datos mínimos existen
    And la API arranca

  Scenario: Seeder ejecutado dos veces
    Given una base ya sembrada
    When se ejecutan los seeders de nuevo
    Then el número de registros no cambia

  Scenario: Rollback completo
    Given una base migrada
    When se ejecuta downgrade hasta la base vacía
    Then no quedan tablas ni restricciones huérfanas

  Scenario: Catálogos mínimos
    Given una base vacía
    When se ejecuta el seeder
    Then existen los 14 alérgenos de la Unión Europea
    And existen los permisos del briefing
    And existen los cinco roles del briefing
