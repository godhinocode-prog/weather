from flask import Flask

app =  Flask(__name__)

html = """
<h1>Hello</h1>

"""

@app.route("/")
def home():
    return html

app.run(
        host=os.environ.get('HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', 5000)),
        debug=True
    )
