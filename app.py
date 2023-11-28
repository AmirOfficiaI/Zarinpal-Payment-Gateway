import mysql.connector
from requests import post
from flask import Flask, url_for, redirect, request, render_template
from config import MMERCHANT_ID, db

app = Flask(__name__)

# Define transaction details
amount = 10000 # Amount based on Rial & required
description = u'توضیحات تراکنش تست' # Description required
email = 'user@gmail.com' # Email optional
mobile = '09123456789' # Phone number optional

# Temporary storage for user ID
user = {}

@app.route("/")
def hello_world():
    return render_template('index.html')


@app.route('/request/')
def send_request():

    # Prepare payment request 
    payload = {
        "merchant_id": MMERCHANT_ID,
        "amount": amount,
        "callback_url": str(url_for('verify', _external=True)),
        "description": description,
        "metadata": {
            "mobile": mobile,
            "email": email
        }
    }

    # Set request headers
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # Send payment request to Zarinpal API
    result = post(
        url='https://api.zarinpal.com/pg/v4/payment/request.json',
        json=payload,
        headers=headers
    )

    # Handle successful payment request
    if result.json()["data"]["code"] == 100:

        user[result.json()["data"]["authority"]] = request.args['User']
        
        return redirect('https://www.zarinpal.com/pg/StartPay/' + result.json()["data"]["authority"])
    
    # Handle failed payment request
    else:
        return 'Something wrong happend. Please try again later...'


@app.route('/verify/', methods=['GET', 'POST'])
def verify():

    # Handle OK payment request
    if request.args.get('Status') == 'OK':

        # Prepare payment request 
        payload = {
            "merchant_id": MMERCHANT_ID,
            "amount": amount,
            "authority": request.args['Authority']
        }

        # Set request headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Send payment verification to Zarinpal API
        result = post(
            url="https://api.zarinpal.com/pg/v4/payment/verify.json",
            json=payload,
            headers=headers
        )

        # Handle successful new payment
        if result.json()["data"]["code"] == 100:

            # Add payment amount to user
            with mysql.connector.connect(**db) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"UPDATE users SET balance = balance + {amount} WHERE id = {user[request.args['Authority']]}")
                    connection.commit()
            
            # Delete user authority and ID from dict
            del user[request.args['Authority']]

            return render_template('success.html')
        
        # Handle successful old payment
        elif result.json()["data"]["code"] == 101:
            return render_template('already.html')
        
        # Handle failed payment
        else:
            return render_template('failed.html')
        
    # Handle NOK payment request
    else:
        return render_template('failed.html')

# Run app
if __name__ == '__main__':
    app.run(debug=True)
