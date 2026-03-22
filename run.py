from app import create_app

app = create_app()  # L'objet DOIT s'appeler 'app'

if __name__ == "__main__":
    # host='0.0.0.0' ouvre l'accès au réseau local
    app.run(host='0.0.0.0', port=5007)