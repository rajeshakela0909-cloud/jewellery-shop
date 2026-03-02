from flask import Flask, render_template_string

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>Jewellery Shop App Live ✅</h1>
    <p>Your Render deployment is successful.</p>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
