### Before to start.

# EVA account
You need an account in (EVA) Syntphony Conversational Experience https://www.eva.bot
The login site is https://[REGION].admin.bot/login

# Get the code
git clone https://github.com/Syntphony-EVA-unofficial/meta-whatsapp-api.git
You will need to create/fill with variables and keys a file called variables.env, you can modify variable.env.template as guideline

### Facebook/Meta setup 
1. You will need a Facebook bussines account, https://business.facebook.com/
2. You will need a Meta developer account, https://developers.facebook.com/
3. Create an app
 * In "my apps" in the developer account, 
    ![App Creation1](/tutorial%20pictures/create%20app1.png) 
* For app type, select Bussines
* If you also login in the Bussines account and the developer account at the same time, the option Bussines Portfolio will show the "Bussines Name" ![App Creation2](/tutorial%20pictures/create%20app2.png)
    
4. Once the APP is created, in the dashboard Set up whatsapp ![Setup wsp 1](/tutorial%20pictures/setup%20wsp%201.png)

5. The whatsapp menu will appear on Left side, under API Setup, add the new Phone Number
![add phone](/tutorial%20pictures/add%20phone%20number%201.png)

* Fill the Bussines information that will appear in the Whatsapp profile and add the number and validation method. 
![fill number](/tutorial%20pictures/add%20phone%20number%202.png)

* There are many ways to get a number, the most easy is to get a SIM Card, also, services like SkypeNumber, BuyIDDNumber.com forwarding another number or any other virtual Number that can receive a phone call or an SMS to verify and connect to Meta.

6. In the Bussines.facebook.com site, go to bussines setting ![bussines setting](/tutorial%20pictures/get%20token1.png)
* Under User/System, create an account (this can be for example an admin service account) 
Generate a token selecting the App and the permisions for the token. 
* Select Never in Token Expiration ![get token2](/tutorial%20pictures/generate%20token4.png)
* After create a system user, press Assign assets and give full control of the app
![](/tutorial%20pictures/add%20asset.png)

7. Going back to developer account, from the side menu Whatsapp/API Setup, copy and save for later the **Phone number ID** ![get phoneid](/tutorial%20pictures/numberid2.png)

8. From the side menu App Setting/Basic, fill in variables.env **APP_ID** and **APP_SECRET** ![get appid](/tutorial%20pictures/app%20secret.png)

8. From the side menu App Setting/Advanced, copy and save for later API version

This concludes the setup using the Meta developer account for Now. Now is time to deploy the server

### Deploy server

9. For testing purposes, you may use ngrok, for deployment you can choose a cloud services like Google CloudRuns

For ngrok use this command:
ngrok http --domain=yourngrokurl.ngrok-free.app 8000

You can buy or get a free static ngrok url

For google cloud run use this commands:

TODO: write instructions

### Configure webhook server in Meta for Developer

10. From the side menu Whatsapp/Configuration:
* Add the webhook callback URL, it may be something like: "https://yourapplication.app/webhook"
* Add any "verification token" of your choice, fill in **VERIFICATION_TOKEN** in variables.env
* To verify the wehbook, you need to have the server running

11. After verify the webhook, go to webhook fields and suscribe to messages
![suscribe messages](/tutorial%20pictures/suscribe%20messages.png)

### Add templates

Not every message and style can be send without templates.
To create a template go to *Bussines Settings*, *Whatsapp Account* and then *Whatsapp Manager*.
In the Whatsapp account you want to manage, click the 3-dot menu icon and then *Manage Whatsapp templates*
Create the message templates you need. 
In the eva bots you will need the *Template name*, the *Language* and fill the variables you declare if any.
Also check on the *Namespace* since this is required
check this, https://developers.facebook.com/docs/whatsapp/api/messages/message-templates/






