# language: es
Característica: Gestión administrativa de usuarios (OICO-61, OICO-62 y OICO-63)

  Antecedentes:
    Dado un administrador autenticado y asociado a un restaurante

  Escenario: Crear un trabajador con un rol del restaurante
    Dado que el administrador tiene el permiso user:manage
    Y existe un rol de camarero para su restaurante
    Cuando solicita crear un usuario con datos válidos y ese role_id
    Entonces la respuesta tiene estado 201 y los campos públicos del usuario
    Y la contraseña se guarda únicamente como hash
    Y la respuesta no contiene contraseñas, hashes ni tokens

  Escenario: Rechazar un correo duplicado
    Dado que el administrador tiene el permiso user:manage
    Y ya existe un usuario con el correo ana@example.com
    Cuando solicita crear otro usuario con el correo ANA@example.com
    Entonces la respuesta tiene estado 409
    Y el mensaje es "Ya existe un usuario con ese correo electrónico."
    Y no se guarda ningún usuario adicional

  Esquema del escenario: Rechazar solicitudes sin permiso
    Dado que el administrador no tiene el permiso user:manage
    Cuando solicita <metodo> sobre /api/v1/users
    Entonces la respuesta tiene estado 403
    Y los usuarios permanecen sin cambios

    Ejemplos:
      | metodo |
      | GET    |
      | POST   |

  Escenario: Listar únicamente los usuarios del restaurante con paginación
    Dado que el administrador tiene el permiso user:manage
    Y existen usuarios en su restaurante y en otro restaurante
    Cuando solicita GET /api/v1/users con page 2 y page_size 1
    Entonces la respuesta tiene estado 200 y la segunda página ordenada por ID
    Y el total y los resultados solo incluyen usuarios de su restaurante
    Y la respuesta no contiene hashes ni tokens

  Escenario: Rechazar datos de creación inválidos
    Dado que el administrador tiene el permiso user:manage
    Cuando solicita crear un usuario con un correo inválido
    Entonces la respuesta tiene estado 422
    Y no se guarda el usuario

  Escenario: Impedir que el cliente elija el restaurante al crear un usuario
    Dado que el administrador tiene el permiso user:manage
    Cuando envía restaurant_id en el cuerpo de la solicitud de creación
    Entonces la respuesta tiene estado 422
    Y no se guarda el usuario

  Escenario: Rechazar un rol de otro restaurante
    Dado que el administrador tiene el permiso user:manage
    Cuando solicita crear un usuario con un role_id de otro restaurante
    Entonces la respuesta tiene estado 404
    Y el mensaje es "El rol solicitado no existe."
    Y no se guarda el usuario

  Escenario: Impedir la creación de un superadministrador
    Dado que el administrador tiene el permiso user:manage
    Cuando solicita crear un usuario con el rol de superadministrador
    Entonces la respuesta tiene estado 403
    Y el mensaje es "No está permitido asignar el rol de superadministrador."
    Y no se guarda el usuario

  Escenario: Devolver una página vacía después del último usuario
    Dado que el administrador tiene el permiso user:manage
    Y su restaurante tiene un usuario
    Cuando solicita GET /api/v1/users con page 2 y page_size 1
    Entonces la respuesta tiene estado 200 y una lista items vacía
    Y el total es 1

  Esquema del escenario: Rechazar una paginación inválida
    Dado que el administrador tiene el permiso user:manage
    Cuando solicita GET /api/v1/users con <parametro> igual a <valor>
    Entonces la respuesta tiene estado 422

    Ejemplos:
      | parametro | valor    |
      | page      | 0        |
      | page_size | 101      |
      | page      | inválido |

  Esquema del escenario: Rechazar solicitudes sin autenticación
    Dado que la solicitud no tiene una autenticación válida
    Cuando solicita <metodo> sobre /api/v1/users
    Entonces la respuesta tiene estado 401

    Ejemplos:
      | metodo |
      | GET    |
      | POST   |

  Escenario: Rechazar un restaurante elegido por el cliente al listar
    Dado que el administrador tiene el permiso user:manage
    Cuando solicita GET /api/v1/users con un parámetro de consulta restaurant_id
    Entonces la respuesta tiene estado 422

  Escenario: Resolver el restaurante desde la cuenta persistida
    Dado que el administrador tiene el permiso user:manage
    Y el restaurante indicado en el token difiere del restaurante de la cuenta persistida
    Cuando solicita GET /api/v1/users sin un parámetro de restaurante
    Entonces la respuesta tiene estado 200
    Y los resultados solo contienen usuarios del restaurante de la cuenta persistida

  Escenario: Editar datos sin modificar los campos omitidos
    Dado que el administrador tiene el permiso user:manage
    Cuando cambia el nombre y el teléfono de un usuario de su restaurante
    Entonces la respuesta tiene estado 200
    Y conserva el correo, la contraseña y el rol anteriores
    Y las sesiones existentes siguen siendo válidas

  Escenario: Cambiar una contraseña y revocar las sesiones
    Dado que el administrador tiene el permiso user:manage
    Cuando establece una contraseña nueva para un trabajador de su restaurante
    Entonces la contraseña se guarda como hash
    Y el trabajador puede iniciar sesión con la contraseña nueva
    Y sus tokens anteriores reciben 401

  Escenario: Rechazar cualquier cambio del rol propio
    Dado que el administrador tiene el permiso user:manage
    Cuando solicita cambiar su propio rol
    Entonces la respuesta tiene estado 403
    Y su rol permanece sin cambios

  Escenario: Cambiar el rol único de otro trabajador
    Dado que el administrador tiene el permiso user:manage
    Cuando asigna a otro trabajador un rol existente de su restaurante
    Entonces la respuesta tiene estado 200
    Y el rol nuevo sustituye al anterior
    Y los tokens anteriores del trabajador reciben 401

  Escenario: Inactivar sin borrar el historial
    Dado un trabajador con reservas registradas y un token vigente
    Cuando el administrador autorizado lo inactiva
    Entonces la respuesta tiene estado 200
    Y la fila del trabajador y sus reservas siguen existiendo
    Y su inicio de sesión recibe 401
    Y su token anterior recibe 401

  Escenario: Reactivar no recupera sesiones anteriores
    Dado un trabajador inactivo con tokens emitidos antes de su baja
    Cuando el administrador autorizado lo reactiva
    Entonces el trabajador puede iniciar una sesión nueva
    Y sus tokens anteriores siguen recibiendo 401

  Escenario: Rechazar un token anterior al contrato de revocación
    Dado un token sin token_version
    Cuando se utiliza para acceder a una ruta autenticada
    Entonces la respuesta tiene estado 401
