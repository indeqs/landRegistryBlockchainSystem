// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.0;

/// @title Land Registry Smart Contract
/// @notice This contract allows users to register, buy, and manage lands on the blockchain.
/// @dev Implements land ownership, transactions, and sale status management.
contract landRegistry {
    /// @notice Represents a land record.
    struct Land {
        uint256 id; // Unique ID of the land
        address owner; // Address of the land owner
        string title; // Title of the land
        string location; // Location of the land
        string description; // Description of the land
        uint256 price; // Price of the land in wei
        bool forSale; // Indicates if the land is for sale
        uint256 registrationDate; // Timestamp of when the land was registered
    }

    /// @notice Represents a transaction record.
    struct Transaction {
        uint256 landId; // ID of the land involved in the transaction
        address seller; // Address of the seller
        address buyer; // Address of the buyer
        uint256 price; // Price of the land in wei
        uint256 transactionDate; // Timestamp of the transaction
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
    event LandRegistered(
        uint256 indexed landId,
        address indexed owner,
        uint256 timestamp
    );
    event LandTransferred(
        uint256 indexed landId,
        address indexed from,
        address indexed to,
        uint256 price,
        uint256 timestamp
    );
    event LandStatusChanged(
        uint256 indexed landId,
        bool forSale,
        uint256 timestamp
    );
    event LandPriceChanged(
        uint256 indexed landId,
        uint256 newPrice,
        uint256 timestamp
    );

    // Modifiers
    modifier onlyLandOwner(uint256 _landId) {
        require(
            lands[_landId].owner == msg.sender,
            "Only the land owner can perform this action"
        );
        _;
    }

    modifier landExists(uint256 _landId) {
        require(lands[_landId].owner != address(0), "Land does not exist");
        _;
    }

    /// @notice Registers a new land.
    /// @param _title The title of the land.
    /// @param _location The location of the land.
    /// @param _description A brief description of the land.
    /// @param _price The price of the land in wei.
    /// @param _forSale Indicates whether the land is for sale.
    /// @return The ID of the newly registered land.
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

    /// @notice Allows a user to buy a land that is for sale.
    /// @param _landId The ID of the land to buy.
    /// @dev The buyer must send the exact price of the land in wei.
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
        transactions.push(
            Transaction({
                landId: _landId,
                seller: previousOwner,
                buyer: msg.sender,
                price: land.price,
                transactionDate: block.timestamp
            })
        );

        // Transfer payment to the seller
        payable(previousOwner).transfer(msg.value);

        emit LandTransferred(
            _landId,
            previousOwner,
            msg.sender,
            land.price,
            block.timestamp
        );
    }

    /// @notice Toggles the sale status of a land.
    /// @param _landId The ID of the land.
    /// @param _forSale The new sale status of the land.
    function toggleForSale(
        uint256 _landId,
        bool _forSale
    ) external onlyLandOwner(_landId) landExists(_landId) {
        lands[_landId].forSale = _forSale;
        emit LandStatusChanged(_landId, _forSale, block.timestamp);
    }

    /// @notice Changes the price of a land.
    /// @param _landId The ID of the land.
    /// @param _newPrice The new price of the land in wei.
    function changeLandPrice(
        uint256 _landId,
        uint256 _newPrice
    ) external onlyLandOwner(_landId) landExists(_landId) {
        require(_newPrice > 0, "Price must be greater than zero");
        lands[_landId].price = _newPrice;
        emit LandPriceChanged(_landId, _newPrice, block.timestamp);
    }

    /// @notice Removes a land from the owner's list of owned lands.
    /// @param _owner The address of the owner.
    /// @param _landId The ID of the land to remove.
    function removeFromOwnedLands(address _owner, uint256 _landId) internal {
        uint256[] storage ownedLands = landsByOwner[_owner];
        for (uint256 i = 0; i < ownedLands.length; i++) {
            if (ownedLands[i] == _landId) {
                ownedLands[i] = ownedLands[ownedLands.length - 1];
                ownedLands.pop();
                break;
            }
        }
    }

    /// @notice Retrieves all lands owned by a specific address.
    /// @param _owner The address of the owner.
    /// @return An array of land IDs owned by the specified address.
    function getLandsByOwner(
        address _owner
    ) external view returns (uint256[] memory) {
        return landsByOwner[_owner];
    }

    /// @notice Retrieves the total number of transactions.
    /// @return The total number of transactions recorded in the contract.
    function getTransactionCount() external view returns (uint256) {
        return transactions.length;
    }
}
