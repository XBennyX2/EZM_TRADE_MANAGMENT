# SendGrid Email Setup for EZM Trade Management

This guide will help you set up SendGrid for reliable email delivery in the EZM Trade Management system.

## Why SendGrid?

- **Reliable Delivery**: 99%+ delivery rate
- **Scalable**: Handle thousands of emails
- **Analytics**: Track email opens, clicks, bounces
- **Professional**: Avoid spam folders
- **Free Tier**: 100 emails/day free forever

## Step 1: Create SendGrid Account

1. Go to [SendGrid.com](https://sendgrid.com/)
2. Click "Start for Free"
3. Sign up with your email
4. Verify your email address
5. Complete the account setup

## Step 2: Get API Key

1. Log into your SendGrid dashboard
2. Go to **Settings** → **API Keys**
3. Click **Create API Key**
4. Choose **Restricted Access**
5. Give it a name like "EZM Trade Management"
6. Under **Mail Send**, select **Full Access**
7. Click **Create & View**
8. **IMPORTANT**: Copy the API key immediately (you won't see it again!)

## Step 3: Verify Sender Identity

### Option A: Single Sender Verification (Easiest)
1. Go to **Settings** → **Sender Authentication**
2. Click **Verify a Single Sender**
3. Fill in your details:
   - From Name: "EZM Trade Management"
   - From Email: your-email@yourdomain.com
   - Reply To: same as from email
   - Company Address: your company address
4. Click **Create**
5. Check your email and click the verification link

### Option B: Domain Authentication (Recommended for Production)
1. Go to **Settings** → **Sender Authentication**
2. Click **Authenticate Your Domain**
3. Enter your domain (e.g., yourdomain.com)
4. Follow the DNS setup instructions
5. Wait for verification (can take up to 48 hours)

## Step 4: Configure EZM Trade Management

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your SendGrid API key:
   ```env
   SENDGRID_API_KEY=SG.your-actual-api-key-here
   DEFAULT_FROM_EMAIL=your-verified-email@yourdomain.com
   ```

3. Restart your Django server:
   ```bash
   python manage.py runserver
   ```

## Step 5: Test Email Functionality

### Test 1: Create a New User
1. Log in as admin
2. Go to User Management
3. Create a new user
4. Check if the welcome email is sent

### Test 2: Reset User Account
1. Go to User Management
2. Click the reset button for a user
3. Check if the reset email is sent

### Test 3: Check SendGrid Dashboard
1. Go to your SendGrid dashboard
2. Check **Activity** → **Email Activity**
3. You should see your sent emails

## Troubleshooting

### Common Issues

**1. "Forbidden" Error**
- Check your API key permissions
- Ensure "Mail Send" has "Full Access"

**2. "Sender Not Verified"**
- Complete sender verification process
- Use the exact email address you verified

**3. Emails Not Delivered**
- Check SendGrid Activity dashboard
- Look for bounces or blocks
- Verify recipient email addresses

**4. "Authentication Failed"**
- Double-check your API key
- Ensure no extra spaces in .env file
- Restart Django server after changes

### Email Delivery Best Practices

1. **Use Professional From Address**
   - Use your domain: noreply@yourdomain.com
   - Avoid generic emails like gmail.com

2. **Set Up SPF/DKIM Records**
   - Complete domain authentication
   - Improves deliverability

3. **Monitor Reputation**
   - Check SendGrid reputation dashboard
   - Keep bounce rate < 5%
   - Keep spam rate < 0.1%

## Production Considerations

### Security
- Store API key in environment variables
- Never commit API keys to version control
- Use restricted API keys with minimal permissions

### Monitoring
- Set up SendGrid webhooks for delivery tracking
- Monitor email metrics in SendGrid dashboard
- Set up alerts for delivery issues

### Scaling
- SendGrid free tier: 100 emails/day
- Paid plans start at $14.95/month for 40,000 emails
- Consider upgrading based on your needs

## Support

- **SendGrid Documentation**: https://docs.sendgrid.com/
- **SendGrid Support**: Available in dashboard
- **EZM Trade Management**: Check application logs for detailed error messages

## Alternative Email Services

If SendGrid doesn't work for you, the system also supports:

1. **Mailgun**: Similar setup process
2. **Amazon SES**: AWS-based email service
3. **Gmail SMTP**: For development/small scale
4. **Custom SMTP**: Any SMTP server

To use alternatives, update the EMAIL_* settings in your .env file instead of SENDGRID_API_KEY.
