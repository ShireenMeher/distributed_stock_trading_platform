# create virtual env
python3 -m venv venv
source venv/bin/activate

# install all requirements
pip install -r src/client/requirements.txt
pip install -r src/order_service/requirements.txt
pip install -r src/catelog_service/requirements.txt
pip install -r src/frontend_service/requirements.txt

# run the servers
python3 src/frontend_service/src/main.py 
python3 src/catelog_service/src/main.py 
python3 src/order_service/src/main.py 


# run client
./run_latency_lookup.sh
./run_latency_trade.sh
python3 plot_latency_graphs.py
