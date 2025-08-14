<h1>📚 sf_email_bot</h1>
Automated Email Notifications for New Book Releases<br><br>

This Python application monitors The Broken Binding's shops (To the Stars, Dragon's Hoard, and The Infirmary) and sends email alerts when new special or limited edition books are added. It compares the list of items from the most recent previous run to the current run and triggers an email if any new or changed items are found.

<h1>🚀 Features</h1>
<ul>
  <li><b>Automated Monitoring:</b> Periodically checks specified pages for new book listings.</li>
  <li><b>Email Alerts:</b> Sends notifications containing the title and price of newly added or changed books.</li>
  <li><b>AWS Lambda Deployment:</b> Runs as a serverless function, triggered at regular intervals via AWS EventBridge.</li>
  <li><b>Continuous Deployment:</b> Integration with GitHub Actions for automated deployments to AWS Lambda.</li>
</ul>

<h1>🛠️ Installation Notes</h1>    
A <code>requirements.txt</code> file is included for installing necessary dependencies after cloning.<br><br>

<b>Create a <code>.env</code> file or set the following environment variables:</b>
<ul>
  <li><b>BUCKET_NAME:</b> The S3 bucket used to save/load the item list from the previous run.</li>
  <li><b>FILE_PATH:</b> The S3 directory path for the stored item file.</li>
  <li><b>RECIPIENT_EMAILS:</b> The email addresses that should receive book alerts.</li>
  <li><b>SF_EMAIL_USERNAME:</b> The email account used to send notifications.</li>
  <li><b>SF_EMAIL_PASSWORD:</b> The password (or app password) for the sending email account.</li>
</ul>

<h1>🔧 Future Enhancements</h1>
<ul>
  <li><b>Database Integration:</b> Use AWS RDS to track products more efficiently and support multiple users/emails.</li>
  <li><b>Multi-Site Monitoring:</b> Extend support to monitor additional bookseller sites.</li>
  <li><b>Front-end Interface:</b> Create a webpage for users to sign up, log in, and manage alert preferences.</li>
  <li><b>User Authentication Management:</b> Use AWS Cognito to handle secure sign-up and sign-in workflows.</li>
  <li><b>Email Enhancements:</b> Migrate to AWS SES for more reliable and scalable email delivery.</li>
  <li><b>Additional Sites:</b> Add scraping modules for more special edition book retailers.</li>
  <li><b>Analytics:</b> Build dashboards for email engagement and scraper timing/efficacy.</li>
</ul>

<h1>🤝 Contributing</h1>
Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.
