from flask import Flask, render_template

app = Flask(__name__)


@app.get("/")
def index():
    return render_template(
        "index.html", values={}, errors={}, result=None, rows=[], region_label=None
    )


if __name__ == "__main__":
    app.run(debug=False, port=5000)
