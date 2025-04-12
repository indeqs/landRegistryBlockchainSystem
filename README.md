# Land Registry Blockchain System

A Flask-based web application for managing land registry records using blockchain technology. This system ensures secure, transparent, and tamper-proof land ownership records.

## How to run

1. Clone the repository:
```bash
git clone https://github.com/indeqs/landRegistryBlockchainSystem.git
```
2. Move into the directory:
```bash
cd landRegistryBlockchainSystem
```

3. Create a virtual environment:
```bash
python3 -m venv env
source env/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Set up the following environment variables:
```bash
SECRET="Rbaz%RVbuu27@Te*MEF0*Bc05WaU7JDND8#YR1pdm!XA!UtSpNb#wPQu1F4*Vn&R"
RPC_URL="https://base-sepolia-rpc.publicnode.com"
```

- The `RPC_URL` we're using here is a public one so transactions might be slow. For faster transactions, use an RPC URL from providers like [alchemy](https://www.alchemy.com/) or [infura](https://www.infura.io/)

6. Run the application:
```bash
python3 app.py
```

- Visit [localhost](http://127.0.0.1:5000) in your browser.