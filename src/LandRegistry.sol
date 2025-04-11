// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract LandRegistry {
    struct Land {
        uint256 id;
        address owner;
        uint256 price;
        string location;
        string description;
        string imageHash;
        bool forSale;
    }

    struct User {
        string name;
        string email;
        string profileImageHash;
        bool isRegistered;
    }

    mapping(uint256 => Land) public lands;
    mapping(address => User) public users;
    mapping(address => uint256[]) public userLands;

    uint256 public landCounter = 0;

    event UserRegistered(address indexed userAddress, string name);
    event LandRegistered(uint256 indexed landId, address indexed owner);
    event LandOffered(uint256 indexed landId, uint256 price);
    event LandSold(
        uint256 indexed landId,
        address indexed oldOwner,
        address indexed newOwner,
        uint256 price
    );
    event ProfileUpdated(address indexed userAddress, string profileImageHash);

    modifier onlyRegistered() {
        require(users[msg.sender].isRegistered, "User not registered");
        _;
    }

    modifier onlyLandOwner(uint256 _landId) {
        require(lands[_landId].owner == msg.sender, "Not the land owner");
        _;
    }

    function registerUser(
        string memory _name,
        string memory _email,
        string memory _profileImageHash
    ) public {
        require(!users[msg.sender].isRegistered, "User already registered");

        users[msg.sender] = User({
            name: _name,
            email: _email,
            profileImageHash: _profileImageHash,
            isRegistered: true
        });

        emit UserRegistered(msg.sender, _name);
    }

    function updateProfile(
        string memory _profileImageHash
    ) public onlyRegistered {
        users[msg.sender].profileImageHash = _profileImageHash;
        emit ProfileUpdated(msg.sender, _profileImageHash);
    }

    function registerLand(
        string memory _location,
        string memory _description,
        string memory _imageHash,
        uint256 _price,
        bool _forSale
    ) public onlyRegistered {
        landCounter++;

        lands[landCounter] = Land({
            id: landCounter,
            owner: msg.sender,
            price: _price,
            location: _location,
            description: _description,
            imageHash: _imageHash,
            forSale: _forSale
        });

        userLands[msg.sender].push(landCounter);
        emit LandRegistered(landCounter, msg.sender);

        if (_forSale) {
            emit LandOffered(landCounter, _price);
        }
    }

    function offerLandForSale(
        uint256 _landId,
        uint256 _price
    ) public onlyRegistered onlyLandOwner(_landId) {
        Land storage land = lands[_landId];
        land.forSale = true;
        land.price = _price;

        emit LandOffered(_landId, _price);
    }

    function buyLand(uint256 _landId) public payable onlyRegistered {
        Land storage land = lands[_landId];

        require(land.forSale, "Land not for sale");
        require(msg.value >= land.price, "Insufficient funds");
        require(land.owner != msg.sender, "Already owner");

        address previousOwner = land.owner;

        // Remove land from previous owner's list
        removeFromUserLands(previousOwner, _landId);

        // Transfer ownership
        land.owner = msg.sender;
        land.forSale = false;
        userLands[msg.sender].push(_landId);

        // Transfer funds
        payable(previousOwner).transfer(msg.value);

        emit LandSold(_landId, previousOwner, msg.sender, land.price);
    }

    function removeFromUserLands(address _user, uint256 _landId) internal {
        uint256[] storage lands = userLands[_user];
        for (uint i = 0; i < lands.length; i++) {
            if (lands[i] == _landId) {
                if (i < lands.length - 1) {
                    lands[i] = lands[lands.length - 1];
                }
                lands.pop();
                break;
            }
        }
    }

    function getUserLands(
        address _user
    ) public view returns (uint256[] memory) {
        return userLands[_user];
    }

    function getLandDetails(
        uint256 _landId
    )
        public
        view
        returns (
            uint256 id,
            address owner,
            uint256 price,
            string memory location,
            string memory description,
            string memory imageHash,
            bool forSale
        )
    {
        Land storage land = lands[_landId];
        return (
            land.id,
            land.owner,
            land.price,
            land.location,
            land.description,
            land.imageHash,
            land.forSale
        );
    }

    function getAllLandsForSale() public view returns (uint256[] memory) {
        uint256[] memory forSaleLands = new uint256[](landCounter);
        uint256 count = 0;

        for (uint i = 1; i <= landCounter; i++) {
            if (lands[i].forSale) {
                forSaleLands[count] = i;
                count++;
            }
        }

        // Resize array to actual count
        assembly {
            mstore(forSaleLands, count)
        }

        return forSaleLands;
    }
}
