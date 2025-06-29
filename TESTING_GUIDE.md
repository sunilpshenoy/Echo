# 🧪 COMPREHENSIVE TESTING GUIDE

## 📧 Test Contacts for Email Addition

You can add these test users as contacts using their email addresses:

### Test Users Available:
1. **Alice Johnson**
   - Email: `alice@test.com`
   - PIN: `PIN-ALI001`
   - Profile: 28, Female, San Francisco, CA
   - Bio: "Love hiking and photography. Always up for coffee chats!"

2. **Bob Smith**
   - Email: `bob@test.com`
   - PIN: `PIN-BOB002`
   - Profile: 32, Male, New York, NY
   - Bio: "Tech enthusiast and basketball player. Let's connect!"

3. **Carol Davis**
   - Email: `carol@test.com`
   - PIN: `PIN-CAR003`
   - Profile: 26, Female, Austin, TX
   - Bio: "Artist and yoga instructor. Seeking meaningful connections."

## 🔧 Step-by-Step Testing Instructions

### 1. Add Contacts by Email
1. Go to **Chats** tab
2. Click the **➕** button (Add Contact)
3. Select **📧 Email** tab
4. Enter one of the test emails above (e.g., `alice@test.com`)
5. Click **Add Contact**
6. ✅ You should see "Contact added successfully! 🎉"

### 2. Add Contacts by PIN
1. Go to **Chats** tab
2. Click the **➕** button (Add Contact)
3. Keep **📱 PIN** tab selected (default)
4. Enter one of the test PINs above (e.g., `PIN-ALI001`)
5. Click **Send Request**
6. ✅ You should see "Connection request sent! 🎉"

### 3. Test QR Scanner
1. Go to **Chats** tab
2. Click the **➕** button (Add Contact)
3. Stay on **📱 PIN** tab
4. Click **📷 Scan QR Code**
5. Click **📷 Enable Camera**
6. ✅ You should see camera permission request and helpful instructions

### 4. Test Premium Features
1. Go to **Discover** tab
2. Click **Upgrade to Premium**
3. Click **🚀 Enable Demo Mode (Testing)**
4. Confirm the dialog
5. ✅ Page should reload with premium features enabled

### 5. Test Chatting Features
After adding contacts:
1. Go to **Chats** tab
2. Click on a contact to open chat
3. Type a message and press Enter
4. Click the **⋯** button next to contact name for options:
   - 💬 Chat
   - 📎 Share Files
   - 🎙️ Voice Call
   - 📹 Video Call

### 6. Test Team Creation
1. Go to **Teams** tab
2. Click the **➕** button or **Create Team** button
3. Enter team name and description
4. Click **Create Team**
5. ✅ You should see "Team creation will be implemented soon! 👥"

## 🐛 Debug Console Messages

Open browser Developer Tools (F12) → Console to see debug messages:
- `addContactByEmail called with email: ...`
- `Making API call to add contact...`
- `Contact added successfully: ...`
- `sendConnectionRequest called with PIN: ...`
- `Camera access button clicked`

## ⚠️ Common Issues & Solutions

**Issue**: "Failed to add contact"
**Solution**: Make sure you're using the exact test emails listed above

**Issue**: "Camera access denied"
**Solution**: Enable camera permissions in browser settings, or use PIN method instead

**Issue**: "Connection request failed"
**Solution**: Make sure you're using the exact test PINs listed above

**Issue**: Buttons not responding
**Solution**: Check browser console for JavaScript errors, refresh the page

## 📱 Quick Test Sequence

1. Add Alice by email: `alice@test.com`
2. Add Bob by PIN: `PIN-BOB002`
3. Test QR scanner (camera access)
4. Enable premium demo mode
5. Chat with added contacts
6. Create a test team

All features should now work correctly! 🎉