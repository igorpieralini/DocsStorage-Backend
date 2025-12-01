import mysql.connector
import bcrypt

def check_user(email, password):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="docsstorage"
        )
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email = %s LIMIT 1",
            (email,)
        )
        user = cursor.fetchone()

        if not user:
            return {"success": False, "message": "Usuário não encontrado"}

        if not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            return {"success": False, "message": "Senha incorreta"}

        return {
            "success": True,
            "message": "Login realizado com sucesso",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "created_at": user["created_at"]
            }
        }

    except Exception as e:
        return {"success": False, "message": str(e)}

    finally:
        cursor.close()
        conn.close()
