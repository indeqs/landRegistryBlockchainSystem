// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract LandRegistry {
    struct Land {
        uint256 id;
        address owner;
        string title;
        string location;
        string description;
        uint256 price;
        bool forSale;
        uint256 registrationDate;
    }
    
    struct Transaction {
        uint256 landId;
        address seller;
        address buyer;
        uint256 price;
        uint256 transactionDate;
    }
    
    // Mapping from land ID to Land struct
    mapping(uint256 => Land) public lands;
    
    // Array to store all transaction records
    Transaction[] public transactions;
    
    // Mapping from user address to owned land IDs
    mapping(address => uint256[]) public landsByOwner;
    
    // Counter for land IDs
    uint256 private landIdCounter;
    
    // Events
    event LandRegistered(uint256 indexed landId, address indexed owner, uint256 timestamp);
    event LandTransferred(uint256 indexed landId, address indexed from, address indexed to, uint256 price, uint256 timestamp);
    event LandStatusChanged(uint256 indexed landId, bool forSale, uint256 timestamp);
    event LandPriceChanged(uint256 indexed landId, uint256 newPrice, uint256 timestamp);
    
    // Modifiers
    modifier onlyLandOwner(uint256 _landId) {
        require(lands[_landId].owner == msg.sender, "Only the land owner can perform this action");
        _;
    }
    
    modifier landExists(uint256 _landId) {
        require(lands[_landId].owner != address(0), "Land does not exist");
        _;
    }
    
    // Register a new land
    function registerLand(
        string memory _title,
        string memory _location,
        string memory _description,
        uint256 _price,
        bool _forSale
    ) external returns (uint256) {
        landIdCounter++;
        uint256 newLandId = landIdCounter;
        
        lands[newLandId] = Land({
            id: newLandId,
            owner: msg.sender,
            title: _title,
            location: _location,
            description: _description,
            price: _price,
            forSale: _forSale,
            registrationDate: block.timestamp
        });
        
        landsByOwner[msg.sender].push(newLandId);
        
        emit LandRegistered(newLandId, msg.sender, block.timestamp);
        
        return newLandId;
    }
    
    // Buy land
    function buyLand(uint256 _landId) external payable landExists(_landId) {
        Land storage land = lands[_landId];
        
        require(land.forSale, "Land is not for sale");
        require(land.owner != msg.sender, "Owner cannot buy their own land");
        require(msg.value == land.price, "Incorrect payment amount");
        
        address previousOwner = land.owner;
        
        // Update land ownership
        land.owner = msg.sender;
        land.forSale = false;
        
        // Add land to buyer's owned lands
        landsByOwner[msg.sender].push(_landId);
        
        // Remove land from seller's owned lands
        removeFromOwnedLands(previousOwner, _landId);
        
        // Record transaction
        transactions.push(Transaction({
            landId: _landId,
            seller: previousOwner,
            buyer: msg.sender,
            price: land.price,
            transactionDate: block.timestamp
        }));
        
        // Transfer payment to the seller
        payable(previousOwner).transfer(msg.value);
        
        emit LandTransferred(_landId, previousOwner, msg.sender, land.price, block.timestamp);
    }
    
    // Toggle land for sale status
    function toggleForSale(uint256 _landId, bool _forSale) external{}