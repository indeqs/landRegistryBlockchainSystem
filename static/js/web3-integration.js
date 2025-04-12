// static/js/web3-integration.js

/**
 * Web3 integration for Land Registry blockchain application
 * Handles wallet connection and transaction signing
 */

// Store connected account
let currentAccount = null;
let web3 = null;
let landRegistryContract = null;
const CONTRACT_ADDRESS = '0x322D4Ab5baC728982Fb228CC37f527b599817836';

// Initialize Web3 
async function initWeb3() {
    // Check if MetaMask is installed
    if (window.ethereum) {
        try {
            web3 = new Web3(window.ethereum);

            // Load contract ABI
            const contractABI = [
                {
                    "anonymous": false,
                    "inputs": [
                        {
                            "indexed": true,
                            "internalType": "uint256",
                            "name": "landId",
                            "type": "uint256"
                        },
                        {
                            "indexed": false,
                            "internalType": "uint256",
                            "name": "newPrice",
                            "type": "uint256"
                        },
                        {
                            "indexed": false,
                            "internalType": "uint256",
                            "name": "timestamp",
                            "type": "uint256"
                        }
                    ],
                    "name": "LandPriceChanged",
                    "type": "event"
                },
                {
                    "anonymous": false,
                    "inputs": [
                        {
                            "indexed": true,
                            "internalType": "uint256",
                            "name": "landId",
                            "type": "uint256"
                        },
                        {
                            "indexed": true,
                            "internalType": "address",
                            "name": "owner",
                            "type": "address"
                        },
                        {
                            "indexed": false,
                            "internalType": "uint256",
                            "name": "timestamp",
                            "type": "uint256"
                        }
                    ],
                    "name": "LandRegistered",
                    "type": "event"
                },
                {
                    "anonymous": false,
                    "inputs": [
                        {
                            "indexed": true,
                            "internalType": "uint256",
                            "name": "landId",
                            "type": "uint256"
                        },
                        {
                            "indexed": false,
                            "internalType": "bool",
                            "name": "forSale",
                            "type": "bool"
                        },
                        {
                            "indexed": false,
                            "internalType": "uint256",
                            "name": "timestamp",
                            "type": "uint256"
                        }
                    ],
                    "name": "LandStatusChanged",
                    "type": "event"
                },
                {
                    "anonymous": false,
                    "inputs": [
                        {
                            "indexed": true,
                            "internalType": "uint256",
                            "name": "landId",
                            "type": "uint256"
                        },
                        {
                            "indexed": true,
                            "internalType": "address",
                            "name": "from",
                            "type": "address"
                        },
                        {
                            "indexed": true,
                            "internalType": "address",
                            "name": "to",
                            "type": "address"
                        },
                        {
                            "indexed": false,
                            "internalType": "uint256",
                            "name": "price",
                            "type": "uint256"
                        },
                        {
                            "indexed": false,
                            "internalType": "uint256",
                            "name": "timestamp",
                            "type": "uint256"
                        }
                    ],
                    "name": "LandTransferred",
                    "type": "event"
                },
                {
                    "inputs": [
                        {
                            "internalType": "uint256",
                            "name": "_landId",
                            "type": "uint256"
                        }
                    ],
                    "name": "buyLand",
                    "outputs": [],
                    "stateMutability": "payable",
                    "type": "function"
                },
                {
                    "inputs": [
                        {
                            "internalType": "uint256",
                            "name": "_landId",
                            "type": "uint256"
                        },
                        {
                            "internalType": "uint256",
                            "name": "_newPrice",
                            "type": "uint256"
                        }
                    ],
                    "name": "changeLandPrice",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "inputs": [
                        {
                            "internalType": "address",
                            "name": "_owner",
                            "type": "address"
                        }
                    ],
                    "name": "getLandsByOwner",
                    "outputs": [
                        {
                            "internalType": "uint256[]",
                            "name": "",
                            "type": "uint256[]"
                        }
                    ],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "getTransactionCount",
                    "outputs": [
                        {
                            "internalType": "uint256",
                            "name": "",
                            "type": "uint256"
                        }
                    ],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [
                        {
                            "internalType": "uint256",
                            "name": "",
                            "type": "uint256"
                        }
                    ],
                    "name": "lands",
                    "outputs": [
                        {
                            "internalType": "uint256",
                            "name": "id",
                            "type": "uint256"
                        },
                        {
                            "internalType": "address",
                            "name": "owner",
                            "type": "address"
                        },
                        {
                            "internalType": "string",
                            "name": "title",
                            "type": "string"
                        },
                        {
                            "internalType": "string",
                            "name": "location",
                            "type": "string"
                        },
                        {
                            "internalType": "string",
                            "name": "description",
                            "type": "string"
                        },
                        {
                            "internalType": "uint256",
                            "name": "price",
                            "type": "uint256"
                        },
                        {
                            "internalType": "bool",
                            "name": "forSale",
                            "type": "bool"
                        },
                        {
                            "internalType": "uint256",
                            "name": "registrationDate",
                            "type": "uint256"
                        }
                    ],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [
                        {
                            "internalType": "address",
                            "name": "",
                            "type": "address"
                        },
                        {
                            "internalType": "uint256",
                            "name": "",
                            "type": "uint256"
                        }
                    ],
                    "name": "landsByOwner",
                    "outputs": [
                        {
                            "internalType": "uint256",
                            "name": "",
                            "type": "uint256"
                        }
                    ],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [
                        {
                            "internalType": "string",
                            "name": "_title",
                            "type": "string"
                        },
                        {
                            "internalType": "string",
                            "name": "_location",
                            "type": "string"
                        },
                        {
                            "internalType": "string",
                            "name": "_description",
                            "type": "string"
                        },
                        {
                            "internalType": "uint256",
                            "name": "_price",
                            "type": "uint256"
                        },
                        {
                            "internalType": "bool",
                            "name": "_forSale",
                            "type": "bool"
                        }
                    ],
                    "name": "registerLand",
                    "outputs": [
                        {
                            "internalType": "uint256",
                            "name": "",
                            "type": "uint256"
                        }
                    ],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "inputs": [
                        {
                            "internalType": "uint256",
                            "name": "_landId",
                            "type": "uint256"
                        },
                        {
                            "internalType": "bool",
                            "name": "_forSale",
                            "type": "bool"
                        }
                    ],
                    "name": "toggleForSale",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "inputs": [
                        {
                            "internalType": "uint256",
                            "name": "",
                            "type": "uint256"
                        }
                    ],
                    "name": "transactions",
                    "outputs": [
                        {
                            "internalType": "uint256",
                            "name": "landId",
                            "type": "uint256"
                        },
                        {
                            "internalType": "address",
                            "name": "seller",
                            "type": "address"
                        },
                        {
                            "internalType": "address",
                            "name": "buyer",
                            "type": "address"
                        },
                        {
                            "internalType": "uint256",
                            "name": "price",
                            "type": "uint256"
                        },
                        {
                            "internalType": "uint256",
                            "name": "transactionDate",
                            "type": "uint256"
                        }
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }
            ];

            // Initialize contract
            landRegistryContract = new web3.eth.Contract(contractABI, CONTRACT_ADDRESS);

            // Get connected accounts
            const accounts = await window.ethereum.request({ method: 'eth_accounts' });
            handleAccountsChanged(accounts);

            // Listen for account changes
            window.ethereum.on('accountsChanged', handleAccountsChanged);

            return true;
        } catch (error) {
            console.error("Error initializing Web3:", error);
            return false;
        }
    } else {
        console.warn("Please install MetaMask!");
        return false;
    }
}

// Handle account changes
function handleAccountsChanged(accounts) {
    const walletStatus = document.getElementById('wallet-status');
    const walletAddress = document.getElementById('wallet-address');
    const connectWalletBtn = document.getElementById('connect-wallet-btn');
    const walletRequiredButtons = document.querySelectorAll('.requires-wallet');

    if (accounts.length === 0) {
        // No accounts found or user is disconnected
        currentAccount = null;

        if (walletStatus) walletStatus.className = 'badge bg-danger me-2';
        if (walletStatus) walletStatus.textContent = 'Not Connected';
        if (walletAddress) walletAddress.textContent = 'No wallet connected';
        if (connectWalletBtn) connectWalletBtn.disabled = false;

        // Disable buttons that require wallet connection
        walletRequiredButtons.forEach(button => {
            button.disabled = true;
        });

    } else if (accounts[0] !== currentAccount) {
        // Account changed or first connection
        currentAccount = accounts[0];

        if (walletStatus) walletStatus.className = 'badge bg-success me-2';
        if (walletStatus) walletStatus.textContent = 'Connected';
        if (walletAddress) walletAddress.textContent = `${currentAccount.substring(0, 6)}...${currentAccount.substring(38)}`;
        if (connectWalletBtn) connectWalletBtn.disabled = true;

        // Enable buttons that require wallet connection
        walletRequiredButtons.forEach(button => {
            button.disabled = false;
        });

        // Update user's blockchain address in database
        updateUserWalletAddress(currentAccount);
    }
}

// Connect wallet
async function connectWallet() {
    if (window.ethereum) {
        try {
            // Request account access
            const accounts = await window.ethereum.request({
                method: 'eth_requestAccounts'
            });

            handleAccountsChanged(accounts);
            return accounts[0];
        } catch (error) {
            console.error("User denied account access");
            return null;
        }
    } else {
        alert("Please install MetaMask!");
        return null;
    }
}

// Update user's wallet address in the database
async function updateUserWalletAddress(address) {
    try {
        const response = await fetch('/update_wallet_address', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ address: address }),
        });

        const result = await response.json();
        if (!result.success) {
            console.error("Failed to update wallet address:", result.error);
        }
    } catch (error) {
        console.error("Error updating wallet address:", error);
    }
}

// Register land on blockchain
async function registerLandOnBlockchain(landData) {
    if (!web3 || !landRegistryContract || !currentAccount) {
        return { success: false, error: "Wallet not connected" };
    }

    try {
        // Call the smart contract to register land
        const result = await landRegistryContract.methods.registerLand(
            landData.title,
            landData.location,
            landData.description,
            web3.utils.toWei(landData.price.toString(), 'ether'),
            landData.forSale
        ).send({ from: currentAccount });

        // Extract the blockchain ID from the transaction events
        const blockchainId = result.events?.LandRegistered?.returnValues?.landId;
        if (!blockchainId) {
            throw new Error("Failed to retrieve blockchain ID from transaction.");
        }

        return {
            success: true,
            transactionHash: result.transactionHash,
            blockchainId: blockchainId
        };
    } catch (error) {
        console.error("Error registering land on blockchain:", error);
        return { success: false, error: error.message };
    }
}

// Update land on blockchain
async function updateLandOnBlockchain(landId, landData) {
    if (!web3 || !landRegistryContract || !currentAccount) {
        return { success: false, error: "Wallet not connected" };
    }

    try {
        // Call the smart contract to update land
        const result = await landRegistryContract.methods.updateLand(
            landData.blockchainId,
            landData.title,
            landData.location,
            landData.description,
            web3.utils.toWei(landData.price.toString(), 'ether'),
            landData.forSale
        ).send({ from: currentAccount });

        return {
            success: true,
            transactionHash: result.transactionHash
        };
    } catch (error) {
        console.error("Error updating land on blockchain:", error);
        return { success: false, error: error.message };
    }
}

// Purchase land on blockchain
async function purchaseLandOnBlockchain(blockchainId, price) {
    if (!web3 || !landRegistryContract || !currentAccount) {
        return { success: false, error: "Wallet not connected" };
    }

    try {
        // Call the smart contract to purchase land
        const result = await landRegistryContract.methods.purchaseLand(blockchainId)
            .send({
                from: currentAccount,
                value: web3.utils.toWei(price.toString(), 'ether')
            });

        return {
            success: true,
            transactionHash: result.transactionHash
        };
    } catch (error) {
        console.error("Error purchasing land on blockchain:", error);
        return { success: false, error: error.message };
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async function () {
    // Initialize Web3
    await initWeb3();

    // Setup connect wallet button if it exists
    const connectWalletBtn = document.getElementById('connect-wallet-btn');
    if (connectWalletBtn) {
        connectWalletBtn.addEventListener('click', connectWallet);
    }
});