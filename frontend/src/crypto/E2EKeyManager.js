/**
 * E2E Key Manager for Pulse App
 * Handles secure key storage, backup, and recovery
 */

class E2EKeyManager {
  constructor() {
    this.storageKey = 'pulse_e2e_keys';
    this.backupKey = 'pulse_e2e_backup';
    this.isInitialized = false;
  }

  /**
   * Initialize key manager with user authentication
   */
  async initialize(userPassword, userId) {
    try {
      this.userId = userId;
      this.userPassword = userPassword;

      // Derive storage encryption key from user password
      this.storageKey = await this.deriveStorageKey(userPassword, userId);

      // Try to load existing keys
      const existingKeys = await this.loadKeys();
      
      if (existingKeys) {
        console.log('✅ Existing E2E keys loaded');
        this.isInitialized = true;
        return existingKeys;
      } else {
        console.log('📝 No existing keys found, will generate new ones');
        return null;
      }

    } catch (error) {
      console.error('❌ Key manager initialization failed:', error);
      throw error;
    }
  }

  /**
   * Store E2E encryption keys securely
   */
  async storeKeys(keyBundle) {
    try {
      if (!this.storageKey) {
        throw new Error('Key manager not initialized');
      }

      // Encrypt key bundle before storage
      const encryptedBundle = await this.encryptForStorage(keyBundle);
      
      // Store in multiple locations for redundancy
      localStorage.setItem(this.storageKey, JSON.stringify(encryptedBundle));
      
      // Create encrypted backup
      const backup = await this.createKeyBackup(keyBundle);
      localStorage.setItem(this.backupKey, JSON.stringify(backup));

      console.log('✅ E2E keys stored securely');
      this.isInitialized = true;

    } catch (error) {
      console.error('❌ Failed to store keys:', error);
      throw error;
    }
  }

  /**
   * Load E2E encryption keys
   */
  async loadKeys() {
    try {
      const encryptedData = localStorage.getItem(this.storageKey);
      if (!encryptedData) {
        return null;
      }

      const parsedData = JSON.parse(encryptedData);
      const keyBundle = await this.decryptFromStorage(parsedData);

      console.log('✅ E2E keys loaded successfully');
      return keyBundle;

    } catch (error) {
      console.error('❌ Failed to load keys:', error);
      
      // Try to recover from backup
      try {
        console.log('🔄 Attempting key recovery from backup...');
        return await this.recoverFromBackup();
      } catch (backupError) {
        console.error('❌ Backup recovery also failed:', backupError);
        throw new Error('Unable to load or recover E2E keys');
      }
    }
  }

  /**
   * Update stored keys (for key rotation)
   */
  async updateKeys(updatedKeyBundle) {
    return await this.storeKeys(updatedKeyBundle);
  }

  /**
   * Clear all stored keys (logout/reset)
   */
  async clearKeys() {
    try {
      localStorage.removeItem(this.storageKey);
      localStorage.removeItem(this.backupKey);
      this.isInitialized = false;
      console.log('✅ E2E keys cleared');
    } catch (error) {
      console.error('❌ Failed to clear keys:', error);
      throw error;
    }
  }

  /**
   * Export keys for backup (user-initiated)
   */
  async exportKeysForBackup(backupPassword) {
    try {
      const keyBundle = await this.loadKeys();
      if (!keyBundle) {
        throw new Error('No keys to export');
      }

      // Create a secure backup with user's backup password
      const backupData = await this.createSecureBackup(keyBundle, backupPassword);
      
      console.log('✅ Keys exported for backup');
      return {
        backupData: backupData,
        timestamp: new Date().toISOString(),
        userId: this.userId
      };

    } catch (error) {
      console.error('❌ Key export failed:', error);
      throw error;
    }
  }

  /**
   * Import keys from backup
   */
  async importKeysFromBackup(backupData, backupPassword) {
    try {
      const keyBundle = await this.restoreFromSecureBackup(backupData, backupPassword);
      await this.storeKeys(keyBundle);
      
      console.log('✅ Keys imported from backup successfully');
      return keyBundle;

    } catch (error) {
      console.error('❌ Key import failed:', error);
      throw error;
    }
  }

  /**
   * Verify key integrity
   */
  async verifyKeyIntegrity(keyBundle) {
    try {
      // Check that all required keys are present
      const requiredKeys = ['identityKey', 'signedPreKey', 'signedPreKeySignature'];
      
      for (const key of requiredKeys) {
        if (!keyBundle[key]) {
          throw new Error(`Missing required key: ${key}`);
        }
      }

      // Verify that keys are valid base64
      for (const key of requiredKeys) {
        if (key !== 'signedPreKeySignature') {
          try {
            atob(keyBundle[key]);
          } catch (e) {
            throw new Error(`Invalid key format: ${key}`);
          }
        }
      }

      console.log('✅ Key integrity verified');
      return true;

    } catch (error) {
      console.error('❌ Key integrity check failed:', error);
      return false;
    }
  }

  /**
   * Generate new one-time pre-keys
   */
  async generateNewOneTimePreKeys(count = 10) {
    try {
      const newKeys = [];
      
      for (let i = 0; i < count; i++) {
        const keyPair = await window.crypto.subtle.generateKey(
          {
            name: 'ECDH',
            namedCurve: 'P-256'
          },
          true,
          ['deriveKey', 'deriveBits']
        );

        const publicKey = await window.crypto.subtle.exportKey('spki', keyPair.publicKey);
        newKeys.push({
          id: this.generateKeyId(),
          publicKey: this.arrayBufferToBase64(publicKey),
          keyPair: keyPair
        });
      }

      console.log(`✅ Generated ${count} new one-time pre-keys`);
      return newKeys;

    } catch (error) {
      console.error('❌ One-time pre-key generation failed:', error);
      throw error;
    }
  }

  /**
   * Private helper methods
   */

  async deriveStorageKey(password, userId) {
    const encoder = new TextEncoder();
    const passwordData = encoder.encode(password);
    const salt = encoder.encode(`pulse_storage_salt_${userId}`);

    // Import password as key material
    const keyMaterial = await window.crypto.subtle.importKey(
      'raw',
      passwordData,
      'PBKDF2',
      false,
      ['deriveKey']
    );

    // Derive storage key
    const storageKey = await window.crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: salt,
        iterations: 100000,
        hash: 'SHA-256'
      },
      keyMaterial,
      {
        name: 'AES-GCM',
        length: 256
      },
      false,
      ['encrypt', 'decrypt']
    );

    return storageKey;
  }

  async encryptForStorage(data) {
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const encodedData = new TextEncoder().encode(JSON.stringify(data));

    const encryptedData = await window.crypto.subtle.encrypt(
      {
        name: 'AES-GCM',
        iv: iv
      },
      this.storageKey,
      encodedData
    );

    return {
      encryptedData: this.arrayBufferToBase64(encryptedData),
      iv: this.arrayBufferToBase64(iv)
    };
  }

  async decryptFromStorage(encryptedBundle) {
    const iv = this.base64ToArrayBuffer(encryptedBundle.iv);
    const encryptedData = this.base64ToArrayBuffer(encryptedBundle.encryptedData);

    const decryptedData = await window.crypto.subtle.decrypt(
      {
        name: 'AES-GCM',
        iv: iv
      },
      this.storageKey,
      encryptedData
    );

    const jsonString = new TextDecoder().decode(decryptedData);
    return JSON.parse(jsonString);
  }

  async createKeyBackup(keyBundle) {
    // Create a redundant backup with additional metadata
    const backupData = {
      keyBundle: keyBundle,
      timestamp: Date.now(),
      userId: this.userId,
      version: '1.0',
      checksum: await this.calculateChecksum(JSON.stringify(keyBundle))
    };

    return await this.encryptForStorage(backupData);
  }

  async createSecureBackup(keyBundle, backupPassword) {
    // Create user-exportable backup with different password
    const backupKey = await this.deriveStorageKey(backupPassword, this.userId + '_backup');
    
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const encodedData = new TextEncoder().encode(JSON.stringify(keyBundle));

    const encryptedData = await window.crypto.subtle.encrypt(
      {
        name: 'AES-GCM',
        iv: iv
      },
      backupKey,
      encodedData
    );

    return {
      encryptedData: this.arrayBufferToBase64(encryptedData),
      iv: this.arrayBufferToBase64(iv),
      algorithm: 'AES-GCM-256',
      iterations: 100000
    };
  }

  async restoreFromSecureBackup(backupData, backupPassword) {
    const backupKey = await this.deriveStorageKey(backupPassword, this.userId + '_backup');
    
    const iv = this.base64ToArrayBuffer(backupData.iv);
    const encryptedData = this.base64ToArrayBuffer(backupData.encryptedData);

    const decryptedData = await window.crypto.subtle.decrypt(
      {
        name: 'AES-GCM',
        iv: iv
      },
      backupKey,
      encryptedData
    );

    const jsonString = new TextDecoder().decode(decryptedData);
    return JSON.parse(jsonString);
  }

  async recoverFromBackup() {
    const backupData = localStorage.getItem(this.backupKey);
    if (!backupData) {
      throw new Error('No backup available');
    }

    const parsedBackup = JSON.parse(backupData);
    const restoredData = await this.decryptFromStorage(parsedBackup);

    // Verify backup integrity
    const expectedChecksum = await this.calculateChecksum(JSON.stringify(restoredData.keyBundle));
    if (expectedChecksum !== restoredData.checksum) {
      throw new Error('Backup integrity check failed');
    }

    return restoredData.keyBundle;
  }

  async calculateChecksum(data) {
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(data);
    const hashBuffer = await window.crypto.subtle.digest('SHA-256', dataBuffer);
    return this.arrayBufferToBase64(hashBuffer);
  }

  generateKeyId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

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
}

export default E2EKeyManager;