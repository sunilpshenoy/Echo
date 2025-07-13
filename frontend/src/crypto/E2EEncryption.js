/**
 * End-to-End Encryption Engine for Pulse App
 * Implements Signal Protocol-style double ratchet with perfect forward secrecy
 */

class E2EEncryption {
  constructor() {
    this.keyPairs = new Map(); // Store key pairs for different conversations
    this.sharedSecrets = new Map(); // Store shared secrets per conversation
    this.messageKeys = new Map(); // Store message keys for forward secrecy
    this.ratchetStates = new Map(); // Store ratchet states per conversation
  }

  /**
   * Initialize E2E encryption for the current user
   */
  async initialize() {
    try {
      // Generate long-term identity key pair for ECDH
      this.identityKeyPair = await this.generateKeyPair();
      
      // Generate signing key pair for ECDSA signatures
      this.signingKeyPair = await this.generateSigningKeyPair();
      
      // Generate signed pre-key for ECDH
      this.signedPreKey = await this.generateKeyPair();
      
      // Sign the pre-key with the signing key (not identity key)
      this.signedPreKeySignature = await this.signData(
        await this.exportPublicKey(this.signedPreKey.publicKey),
        this.signingKeyPair.privateKey
      );

      // Generate one-time pre-keys (bundle of 10)
      this.oneTimePreKeys = [];
      for (let i = 0; i < 10; i++) {
        this.oneTimePreKeys.push(await this.generateKeyPair());
      }

      console.log('✅ E2E Encryption initialized successfully');
      return {
        identityKey: await this.exportPublicKey(this.identityKeyPair.publicKey),
        signingKey: await this.exportPublicKey(this.signingKeyPair.publicKey, 'ECDSA'),
        signedPreKey: await this.exportPublicKey(this.signedPreKey.publicKey),
        signedPreKeySignature: this.signedPreKeySignature,
        oneTimePreKeys: await Promise.all(
          this.oneTimePreKeys.map(kp => this.exportPublicKey(kp.publicKey))
        )
      };
    } catch (error) {
      console.error('❌ E2E Encryption initialization failed:', error);
      throw error;
    }
  }

  /**
   * Generate ECDH key pair for encryption
   */
  async generateKeyPair() {
    return await window.crypto.subtle.generateKey(
      {
        name: 'ECDH',
        namedCurve: 'P-256'
      },
      true, // extractable
      ['deriveKey', 'deriveBits']
    );
  }

  /**
   * Generate signing key pair for authentication
   */
  async generateSigningKeyPair() {
    return await window.crypto.subtle.generateKey(
      {
        name: 'ECDSA',
        namedCurve: 'P-256'
      },
      true,
      ['sign', 'verify']
    );
  }

  /**
   * Export public key to base64 format
   */
  async exportPublicKey(publicKey, algorithm = 'ECDH') {
    const exported = await window.crypto.subtle.exportKey('spki', publicKey);
    return this.arrayBufferToBase64(exported);
  }

  /**
   * Import public key from base64 format
   */
  async importPublicKey(base64Key, algorithm = 'ECDH') {
    const keyData = this.base64ToArrayBuffer(base64Key);
    return await window.crypto.subtle.importKey(
      'spki',
      keyData,
      {
        name: algorithm,
        namedCurve: 'P-256'
      },
      false,
      algorithm === 'ECDH' ? ['deriveKey', 'deriveBits'] : ['verify']
    );
  }

  /**
   * Derive shared secret using ECDH
   */
  async deriveSharedSecret(privateKey, publicKey) {
    const sharedSecret = await window.crypto.subtle.deriveBits(
      {
        name: 'ECDH',
        public: publicKey
      },
      privateKey,
      256 // 256 bits
    );
    return new Uint8Array(sharedSecret);
  }

  /**
   * Derive message encryption key from shared secret using HKDF
   */
  async deriveMessageKey(sharedSecret, salt, info = 'Pulse Message Key') {
    // Import shared secret as key material
    const keyMaterial = await window.crypto.subtle.importKey(
      'raw',
      sharedSecret,
      'HKDF',
      false,
      ['deriveKey']
    );

    // Derive AES-GCM key
    return await window.crypto.subtle.deriveKey(
      {
        name: 'HKDF',
        hash: 'SHA-256',
        salt: salt,
        info: new TextEncoder().encode(info)
      },
      keyMaterial,
      {
        name: 'AES-GCM',
        length: 256
      },
      false,
      ['encrypt', 'decrypt']
    );
  }

  /**
   * Initialize conversation with another user (sender side)
   */
  async initializeConversation(recipientUserId, recipientBundle) {
    try {
      // Import recipient's keys
      const recipientIdentityKey = await this.importPublicKey(recipientBundle.identityKey);
      const recipientSigningKey = await this.importPublicKey(recipientBundle.signingKey, 'ECDSA');
      const recipientSignedPreKey = await this.importPublicKey(recipientBundle.signedPreKey);
      const recipientOneTimePreKey = recipientBundle.oneTimePreKeys.length > 0 
        ? await this.importPublicKey(recipientBundle.oneTimePreKeys[0])
        : null;

      // Verify signed pre-key signature using the signing key
      const isValidSignature = await this.verifySignature(
        recipientBundle.signedPreKey,
        recipientBundle.signedPreKeySignature,
        recipientSigningKey
      );

      if (!isValidSignature) {
        throw new Error('Invalid signed pre-key signature');
      }

      // Generate ephemeral key pair
      const ephemeralKeyPair = await this.generateKeyPair();

      // Perform Triple Diffie-Hellman (3-DH)
      const dh1 = await this.deriveSharedSecret(this.identityKeyPair.privateKey, recipientSignedPreKey);
      const dh2 = await this.deriveSharedSecret(ephemeralKeyPair.privateKey, recipientIdentityKey);
      const dh3 = await this.deriveSharedSecret(ephemeralKeyPair.privateKey, recipientSignedPreKey);
      
      let dh4 = null;
      if (recipientOneTimePreKey) {
        dh4 = await this.deriveSharedSecret(ephemeralKeyPair.privateKey, recipientOneTimePreKey);
      }

      // Combine all DH outputs to create master secret
      const masterSecret = await this.combineDHOutputs(dh1, dh2, dh3, dh4);

      // Initialize double ratchet
      const ratchetState = await this.initializeDoubleRatchet(
        masterSecret,
        await this.exportPublicKey(ephemeralKeyPair.publicKey),
        recipientBundle.signedPreKey
      );

      // Store conversation state
      this.ratchetStates.set(recipientUserId, ratchetState);

      console.log(`✅ E2E conversation initialized with user ${recipientUserId}`);

      return {
        ephemeralPublicKey: await this.exportPublicKey(ephemeralKeyPair.publicKey),
        usedOneTimePreKey: recipientBundle.oneTimePreKeys.length > 0 ? 0 : null
      };

    } catch (error) {
      console.error('❌ Failed to initialize conversation:', error);
      throw error;
    }
  }

  /**
   * Accept conversation initialization (recipient side)
   */
  async acceptConversation(senderUserId, initData, senderIdentityKey) {
    try {
      // Import sender's keys
      const senderIdentity = await this.importPublicKey(senderIdentityKey);
      const ephemeralPublicKey = await this.importPublicKey(initData.ephemeralPublicKey);

      // Find the used one-time pre-key
      let usedOneTimePreKey = null;
      if (initData.usedOneTimePreKey !== null) {
        usedOneTimePreKey = this.oneTimePreKeys[initData.usedOneTimePreKey];
        // Remove used one-time pre-key
        this.oneTimePreKeys.splice(initData.usedOneTimePreKey, 1);
      }

      // Perform Triple Diffie-Hellman (recipient side)
      const dh1 = await this.deriveSharedSecret(this.signedPreKey.privateKey, senderIdentity);
      const dh2 = await this.deriveSharedSecret(this.identityKeyPair.privateKey, ephemeralPublicKey);
      const dh3 = await this.deriveSharedSecret(this.signedPreKey.privateKey, ephemeralPublicKey);

      let dh4 = null;
      if (usedOneTimePreKey) {
        dh4 = await this.deriveSharedSecret(usedOneTimePreKey.privateKey, ephemeralPublicKey);
      }

      // Combine all DH outputs
      const masterSecret = await this.combineDHOutputs(dh1, dh2, dh3, dh4);

      // Initialize double ratchet (recipient side)
      const ratchetState = await this.initializeDoubleRatchet(
        masterSecret,
        initData.ephemeralPublicKey,
        await this.exportPublicKey(this.signedPreKey.publicKey),
        false // recipient
      );

      // Store conversation state
      this.ratchetStates.set(senderUserId, ratchetState);

      console.log(`✅ E2E conversation accepted with user ${senderUserId}`);

    } catch (error) {
      console.error('❌ Failed to accept conversation:', error);
      throw error;
    }
  }

  /**
   * Encrypt message for specific user
   */
  async encryptMessage(recipientUserId, plaintext) {
    try {
      const ratchetState = this.ratchetStates.get(recipientUserId);
      if (!ratchetState) {
        throw new Error('No E2E session found for this user');
      }

      // Advance sending ratchet
      const messageKey = await this.advanceSendingRatchet(ratchetState);

      // Generate random IV
      const iv = window.crypto.getRandomValues(new Uint8Array(12));

      // Encrypt message
      const encodedMessage = new TextEncoder().encode(plaintext);
      const ciphertext = await window.crypto.subtle.encrypt(
        {
          name: 'AES-GCM',
          iv: iv
        },
        messageKey,
        encodedMessage
      );

      const encryptedData = {
        ciphertext: this.arrayBufferToBase64(ciphertext),
        iv: this.arrayBufferToBase64(iv),
        ratchetPublicKey: ratchetState.sendingRatchetPublicKey,
        messageNumber: ratchetState.sendingMessageNumber,
        chainLength: ratchetState.sendingChainLength
      };

      console.log(`✅ Message encrypted for user ${recipientUserId}`);
      return encryptedData;

    } catch (error) {
      console.error('❌ Message encryption failed:', error);
      throw error;
    }
  }

  /**
   * Decrypt message from specific user
   */
  async decryptMessage(senderUserId, encryptedData) {
    try {
      const ratchetState = this.ratchetStates.get(senderUserId);
      if (!ratchetState) {
        throw new Error('No E2E session found for this user');
      }

      // Advance receiving ratchet if needed
      const messageKey = await this.advanceReceivingRatchet(
        ratchetState,
        encryptedData.ratchetPublicKey,
        encryptedData.messageNumber
      );

      // Decrypt message
      const iv = this.base64ToArrayBuffer(encryptedData.iv);
      const ciphertext = this.base64ToArrayBuffer(encryptedData.ciphertext);

      const plaintext = await window.crypto.subtle.decrypt(
        {
          name: 'AES-GCM',
          iv: iv
        },
        messageKey,
        ciphertext
      );

      const decryptedMessage = new TextDecoder().decode(plaintext);
      console.log(`✅ Message decrypted from user ${senderUserId}`);
      return decryptedMessage;

    } catch (error) {
      console.error('❌ Message decryption failed:', error);
      throw error;
    }
  }

  /**
   * Initialize double ratchet algorithm
   */
  async initializeDoubleRatchet(masterSecret, ephemeralPublicKey, signedPreKeyPublic, isSender = true) {
    // Generate root key and chain keys from master secret
    const salt = new Uint8Array(32); // Zero salt for initial derivation
    
    const rootKey = await this.deriveMessageKey(masterSecret, salt, 'Pulse Root Key');
    
    return {
      rootKey: rootKey,
      sendingChainKey: isSender ? await this.deriveMessageKey(masterSecret, salt, 'Pulse Sending Chain') : null,
      receivingChainKey: !isSender ? await this.deriveMessageKey(masterSecret, salt, 'Pulse Receiving Chain') : null,
      sendingRatchetKeyPair: isSender ? await this.generateKeyPair() : null,
      receivingRatchetPublicKey: !isSender ? ephemeralPublicKey : signedPreKeyPublic,
      sendingMessageNumber: 0,
      receivingMessageNumber: 0,
      sendingChainLength: 0,
      receivingChainLength: 0,
      skippedMessageKeys: new Map()
    };
  }

  /**
   * Advance sending ratchet and derive message key
   */
  async advanceSendingRatchet(ratchetState) {
    // Derive message key from chain key
    const messageKey = await this.deriveMessageKey(
      ratchetState.sendingChainKey,
      new TextEncoder().encode(ratchetState.sendingMessageNumber.toString()),
      'Pulse Message Key'
    );

    // Advance chain key for next message
    ratchetState.sendingChainKey = await this.deriveMessageKey(
      ratchetState.sendingChainKey,
      new TextEncoder().encode('chain_advance'),
      'Pulse Chain Advance'
    );

    ratchetState.sendingMessageNumber++;
    ratchetState.sendingChainLength++;

    return messageKey;
  }

  /**
   * Advance receiving ratchet and derive message key
   */
  async advanceReceivingRatchet(ratchetState, newRatchetPublicKey, messageNumber) {
    // Check if we need to perform DH ratchet step
    if (newRatchetPublicKey !== ratchetState.receivingRatchetPublicKey) {
      // Perform DH ratchet step
      await this.performDHRatchetStep(ratchetState, newRatchetPublicKey);
    }

    // Handle out-of-order messages
    if (messageNumber < ratchetState.receivingMessageNumber) {
      // Try to find skipped message key
      const skippedKey = ratchetState.skippedMessageKeys.get(messageNumber);
      if (skippedKey) {
        ratchetState.skippedMessageKeys.delete(messageNumber);
        return skippedKey;
      }
      throw new Error('Message key not found for out-of-order message');
    }

    // Skip ahead to target message number
    while (ratchetState.receivingMessageNumber < messageNumber) {
      const skippedKey = await this.deriveMessageKey(
        ratchetState.receivingChainKey,
        new TextEncoder().encode(ratchetState.receivingMessageNumber.toString()),
        'Pulse Message Key'
      );
      ratchetState.skippedMessageKeys.set(ratchetState.receivingMessageNumber, skippedKey);
      
      ratchetState.receivingChainKey = await this.deriveMessageKey(
        ratchetState.receivingChainKey,
        new TextEncoder().encode('chain_advance'),
        'Pulse Chain Advance'
      );
      
      ratchetState.receivingMessageNumber++;
    }

    // Derive message key for current message
    const messageKey = await this.deriveMessageKey(
      ratchetState.receivingChainKey,
      new TextEncoder().encode(ratchetState.receivingMessageNumber.toString()),
      'Pulse Message Key'
    );

    // Advance for next message
    ratchetState.receivingChainKey = await this.deriveMessageKey(
      ratchetState.receivingChainKey,
      new TextEncoder().encode('chain_advance'),
      'Pulse Chain Advance'
    );
    
    ratchetState.receivingMessageNumber++;

    return messageKey;
  }

  /**
   * Utility functions
   */
  arrayBufferToBase64(buffer) {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }

  base64ToArrayBuffer(base64) {
    const binary = window.atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  async signData(data, privateKey) {
    const signature = await window.crypto.subtle.sign(
      {
        name: 'ECDSA',
        hash: 'SHA-256'
      },
      privateKey,
      typeof data === 'string' ? new TextEncoder().encode(data) : data
    );
    return this.arrayBufferToBase64(signature);
  }

  async verifySignature(data, signature, publicKey) {
    try {
      const signatureBuffer = this.base64ToArrayBuffer(signature);
      const dataBuffer = typeof data === 'string' ? new TextEncoder().encode(data) : data;
      
      return await window.crypto.subtle.verify(
        {
          name: 'ECDSA',
          hash: 'SHA-256'
        },
        publicKey,
        signatureBuffer,
        dataBuffer
      );
    } catch (error) {
      console.error('Signature verification failed:', error);
      return false;
    }
  }

  async combineDHOutputs(dh1, dh2, dh3, dh4 = null) {
    // Combine multiple DH outputs using HKDF
    const combinedLength = dh1.length + dh2.length + dh3.length + (dh4 ? dh4.length : 0);
    const combined = new Uint8Array(combinedLength);
    
    let offset = 0;
    combined.set(dh1, offset);
    offset += dh1.length;
    combined.set(dh2, offset);
    offset += dh2.length;
    combined.set(dh3, offset);
    offset += dh3.length;
    
    if (dh4) {
      combined.set(dh4, offset);
    }

    return combined;
  }

  async performDHRatchetStep(ratchetState, newRatchetPublicKey) {
    // Import new public key
    const newPublicKey = await this.importPublicKey(newRatchetPublicKey);
    
    // Generate new sending ratchet key pair
    const newSendingKeyPair = await this.generateKeyPair();
    
    // Perform DH with new keys
    const dhOutput = await this.deriveSharedSecret(newSendingKeyPair.privateKey, newPublicKey);
    
    // Update ratchet state
    ratchetState.sendingRatchetKeyPair = newSendingKeyPair;
    ratchetState.receivingRatchetPublicKey = newRatchetPublicKey;
    
    // Derive new root and chain keys
    const salt = new Uint8Array(32);
    ratchetState.rootKey = await this.deriveMessageKey(dhOutput, salt, 'Pulse New Root Key');
    ratchetState.sendingChainKey = await this.deriveMessageKey(dhOutput, salt, 'Pulse New Sending Chain');
    
    // Reset chain lengths
    ratchetState.sendingChainLength = 0;
    ratchetState.sendingMessageNumber = 0;
  }
}

// Export for use in components
export default E2EEncryption;