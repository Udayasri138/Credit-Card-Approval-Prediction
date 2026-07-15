from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    income = int(request.form['income'])
    employment = int(request.form['employment'])
    history = request.form['history']

    if income > 500000 and employment >= 2 and history == "good":
        prediction = "✅ Credit Card Approved"
    else:
        prediction = "❌ Credit Card Rejected"

    return render_template('result.html', prediction=prediction)

if __name__ == '__main__':
    app.run(debug=True)