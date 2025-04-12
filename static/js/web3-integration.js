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
            const contract