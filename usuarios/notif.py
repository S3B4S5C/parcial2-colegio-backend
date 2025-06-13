import requests

def enviar_notificaciones_usuarios(usuarios, titulo, cuerpo, data_extra=None):
    """
    Envía una notificación push FCM a todos los usuarios con fb_token.
    - usuarios: lista de instancias de Usuario
    - titulo: string, título de la notificación
    - cuerpo: string, contenido/mensaje
    - data_extra: diccionario opcional con datos extra
    """
    # Reemplaza esto por tu clave real
    FCM_SERVER_KEY = 'AAAAxxxxxxx:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    FCM_URL = 'https://fcm.googleapis.com/fcm/send'

    headers = {
        'Authorization': f'key={FCM_SERVER_KEY}',
        'Content-Type': 'application/json',
    }

    tokens = [u.fb_token for u in usuarios if u.fb_token]

    if not tokens:
        print("Ningún usuario tiene fb_token, no se envió nada.")
        return

    # Puedes mandar de a 1000 tokens por petición (según docs de FCM)
    chunk_size = 900
    for i in range(0, len(tokens), chunk_size):
        batch = tokens[i:i+chunk_size]
        payload = {
            "registration_ids": batch,
            "notification": {
                "title": titulo,
                "body": cuerpo,
                # "sound": "default", # Opcional
            },
            "data": data_extra or {},
            "priority": "high"
        }
        response = requests.post(FCM_URL, json=payload, headers=headers)
        print(f"FCM [{i}:{i+chunk_size}] - status {response.status_code}: {response.text}")

    print(f"Notificaciones enviadas a {len(tokens)} usuarios con fb_token.")
