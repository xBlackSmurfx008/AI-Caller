#!/bin/bash
# Vercel Deployment Setup Script

set -e

echo "🚀 AI Caller - Vercel Deployment Setup"
echo "========================================"
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
else
    echo "✅ Vercel CLI already installed"
fi

echo ""
echo "🔐 Step 1: Login to Vercel"
echo "---------------------------"
vercel login

echo ""
echo "🔗 Step 2: Link Project"
echo "----------------------"
vercel link

echo ""
echo "📝 Step 3: Environment Variables"
echo "---------------------------------"
echo ""
echo "⚠️  IMPORTANT: You need to set environment variables in Vercel Dashboard:"
echo ""
echo "Required variables:"
echo "  - TWILIO_ACCOUNT_SID"
echo "  - TWILIO_AUTH_TOKEN"
echo "  - TWILIO_PHONE_NUMBER"
echo "  - TWILIO_WEBHOOK_URL (will be set after deployment)"
echo "  - OPENAI_API_KEY"
echo "  - OPENAI_MODEL"
echo "  - DATABASE_URL"
echo "  - SECRET_KEY"
echo "  - JWT_SECRET_KEY"
echo ""
echo "Go to: https://vercel.com/dashboard → Your Project → Settings → Environment Variables"
echo ""

read -p "Press Enter after you've set the environment variables..."

echo ""
echo "🚀 Step 4: Deploy to Production"
echo "--------------------------------"
vercel --prod

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next Steps:"
echo "  1. Copy your Vercel URL (e.g., https://ai-caller.vercel.app)"
echo "  2. Update TWILIO_WEBHOOK_URL in Vercel environment variables"
echo "  3. Configure webhooks in Twilio Console:"
echo "     - Voice: https://[your-project].vercel.app/webhooks/twilio/voice"
echo "     - Status: https://[your-project].vercel.app/webhooks/twilio/status"
echo "  4. Test with a call to your Twilio number"
echo ""

