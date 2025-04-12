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
            const response = await fetch('/static/contract_abi.json');
            const contractAbi = await response.json();

            // Initialize contract
            landRegistryContract = new web3.eth.Contract(
                contractAbi,
                CONTRACT_ADDRESS
            );

            // Setup MetaMask account change and disconnect listeners
            setupEventListeners();

            return true;
        } catch (error) {
            console.error("Error initializing Web3:", error);
            displayError("Failed to initialize Web3. Please refresh and try again.");
            return false;
        }
    } else {
        displayError("MetaMask is not installed! Please install MetaMask to use this application.");
        return false;
    }
}

// Set up event listeners for account changes
function setupEventListeners() {
    // Handle account changes
    window.ethereum.on('accountsChanged', function (accounts) {
        if (accounts.length === 0) {
            // User disconnected their wallet
            currentAccount = null;
            updateConnectionUI(false);
        } else if (accounts[0] !== currentAccount) {
            // Account changed
            currentAccount = accounts[0];
            updateConnectionUI(true);
        }
    });

    // Handle chain changes
    window.ethereum.on('chainChanged', function () {
        // Reload the page on network change
        window.location.reload();
    });
}

// Connect wallet
async function connectWallet() {
    try {
        const accounts = await window.ethereum.request({
            method: 'eth_requestAccounts'
        });

        currentAccount = accounts[0];
        updateConnectionUI(true);

        // Update database with wallet address if needed
        await updateUserWalletAddress(currentAccount);

        return currentAccount;
    } catch (error) {
        console.error("Error connecting wallet:", error);
        displayError("Failed to connect wallet: " + error.message);
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

// Update UI based on connection status
function updateConnectionUI(connected) {
    const connectButton = document.getElementById('connect-wallet-btn');
    const walletStatus = document.getElementById('wallet-status');
    const walletAddress = document.getElementById('wallet-address');

    if (connected && currentAccount) {
        // Connected state
        if (connectButton) {
            connectButton.innerText = 'Wallet Connected';
            connectButton.classList.remove('btn-primary');
            connectButton.classList.add('btn-success');
        }

        if (walletStatus) {
            walletStatus.innerText = 'Connected';
            walletStatus.classList.remove('text-danger');
            walletStatus.classList.add('text-success');
        }

        if (walletAddress) {
            // Format address to show first 6 and last 4 characters
            const formattedAddress = `${currentAccount.substring(0, 6)}...${currentAccount.substring(currentAccount.length - 4)}`;
            walletAddress.innerText = formattedAddress;
        }

        // Enable blockchain action buttons
        document.querySelectorAll('.requires-wallet').forEach(el => {
            el.disabled = false;
        });
    } else {
        // Disconnected state
        if (connectButton) {
            connectButton.innerText = 'Connect Wallet';
            connectButton.classList.remove('btn-success');
            connectButton.classList.add('btn-primary');
        }

        if (walletStatus) {
            walletStatus.innerText = 'Not Connected';
            walletStatus.classList.remove('text-success');
            walletStatus.classList.add('text-danger');
        }

        if (walletAddress) {
            walletAddress.innerText = 'No wallet connected';
        }

        // Disable blockchain action buttons
        document.querySelectorAll('.requires-wallet').forEach(el => {
            el.disabled = true;
        });
    }
}

// Register land on blockchain
async function registerLandOnBlockchain(landData) {
    if (!currentAccount) {
        displayError("Please connect your wallet first!");
        return null;
    }

    try {
        // Convert price from USD to Wei
        const priceInWei = web3.utils.toWei(landData.price.toString(), 'ether');

        // Estimate gas for the transaction
        const gasEstimate = await landRegistryContract.methods.registerLand(
            landData.title,
            landData.location,
            landData.description,
            priceInWei,
            landData.forSale
        ).estimateGas({ from: currentAccount });

        // Send transaction
        const tx = await landRegistryContract.methods.registerLand(
            landData.title,
            landData.location,
            landData.description,
            priceInWei,
            landData.forSale
        ).send({
            from: currentAccount,
            gas: Math.floor(gasEstimate * 1.2) // Add 20% buffer
        });

        // Return transaction details
        return {
            success: true,
            transactionHash: tx.transactionHash,
            blockNumber: tx.blockNumber,
            events: tx.events
        };
    } catch (error) {
        console.error("Error registering land on blockchain:", error);
        displayError("Failed to register land: " + error.message);
        return { success: false, error: error.message };
    }
}

// Update land details on blockchain
async function updateLandOnBlockchain(landId, landData) {
    if (!currentAccount) {
        displayError("Please connect your wallet first!");
        return null;
    }

    try {
        // Convert price from USD to Wei
        const priceInWei = web3.utils.toWei(landData.price.toString(), 'ether');

        // Estimate gas for the transaction
        const gasEstimate = await landRegistryContract.methods.updateLand(
            landData.blockchainId,
            landData.title,
            landData.location,
            landData.description,
            priceInWei,
            landData.forSale
        ).estimateGas({ from: currentAccount });

        // Send transaction
        const tx = await landRegistryContract.methods.updateLand(
            landData.blockchainId,
            landData.title,
            landData.location,
            landData.description,
            priceInWei,
            landData.forSale
        ).send({
            from: currentAccount,
            gas: Math.floor(gasEstimate * 1.2) // Add 20% buffer
        });

        // Return transaction details
        return {
            success: true,
            transactionHash: tx.transactionHash,
            blockNumber: tx.blockNumber,
            events: tx.events
        };
    } catch (error) {
        console.error("Error updating land on blockchain:", error);
        displayError("Failed to update land: " + error.message);
        return { success: false, error: error.message };
    }
}

// Buy land on blockchain
async function buyLandOnBlockchain(landId, price) {
    if (!currentAccount) {
        displayError("Please connect your wallet first!");
        return null;
    }

    try {
        // Convert price from USD to Wei
        const priceInWei = web3.utils.toWei(price.toString(), 'ether');

        // Estimate gas for the transaction
        const gasEstimate = await landRegistryContract.methods.buyLand(
            landId
        ).estimateGas({
            from: currentAccount,
            value: priceInWei
        });

        // Send transaction
        const tx = await landRegistryContract.methods.buyLand(
            landId
        ).send({
            from: currentAccount,
            value: priceInWei,
            gas: Math.floor(gasEstimate * 1.2) // Add 20% buffer
        });

        // Return transaction details
        return {
            success: true,
            transactionHash: tx.transactionHash,
            blockNumber: tx.blockNumber,
            events: tx.events
        };
    } catch (error) {
        console.error("Error buying land on blockchain:", error);
        displayError("Failed to buy land: " + error.message);
        return { success: false, error: error.message };
    }
}

// Display error message
function displayError(message) {
    // Create a Bootstrap alert
    const errorAlert = document.createElement('div');
    errorAlert.className = 'alert alert-danger alert-dismissible fade show';
    errorAlert.setAttribute('role', 'alert');
    errorAlert.innerHTML = `
        <strong>Error!</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Add to page
    const container = document.querySelector('.container');
    if (container) {
        container.prepend(errorAlert);

        // Auto dismiss after 5 seconds
        setTimeout(() => {
            errorAlert.classList.remove('show');
            setTimeout(() => errorAlert.remove(), 150);
        }, 5000);
    }
}

// Display success message
function displaySuccess(message) {
    // Create a Bootstrap alert
    const successAlert = document.createElement('div');
    successAlert.className = 'alert alert-success alert-dismissible fade show';
    successAlert.setAttribute('role', 'alert');
    successAlert.innerHTML = `
        <strong>Success!</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Add to page
    const container = document.querySelector('.container');
    if (container) {
        container.prepend(successAlert);

        // Auto dismiss after 5 seconds
        setTimeout(() => {
            successAlert.classList.remove('show');
            setTimeout(() => successAlert.remove(), 150);
        }, 5000);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize Web3
    const initialized = await initWeb3();

    // Setup connect wallet button
    const connectButton = document.getElementById('connect-wallet-btn');
    if (connectButton && initialized) {
        connectButton.addEventListener('click', connectWallet);
    }

    // Check if wallet is already connected (MetaMask remembers connections)
    if (initialized && window.ethereum.selectedAddress) {
        currentAccount = window.ethereum.selectedAddress;
        updateConnectionUI(true);
    } else {
        updateConnectionUI(false);
    }
});