def close_controller(agent_controller):
    # Close the controller
    agent_controller.terminate()
def init_controller(WEBHOOK_HOST = "0.0.0.0",
    WEBHOOK_BASE = "",
    WEBHOOK_PORT = 8022,
    ADMIN_URL = "http://issuer-agent:8021"):
    import time
    import asyncio
    from aries_basic_controller.aries_controller import AriesAgentController

    # Based on the aca-py agent you wish to control
    agent_controller = AriesAgentController(admin_url=ADMIN_URL)
    agent_controller.init_webhook_server(webhook_host=WEBHOOK_HOST,
                                     webhook_port=WEBHOOK_PORT,
                                     webhook_base=WEBHOOK_BASE)
    return agent_controller
def gen_did(agent_controller):
    # Generate a DID
    did_result = agent_controller.wallet.create_did()
    return did_result
def write_did_to_sovrin():
    # write new DID to Sovrin Stagingnet
    import requests
    import json 

    url = 'https://selfserve.sovrin.org/nym'

    payload = {"network":"buildernet","did": did_object["did"],"verkey":did_object["verkey"],"paymentaddr":""}

    # Adding empty header as parameters are being sent in payload
    headers = {}

    r = requests.post(url, data=json.dumps(payload), headers=headers)
    print(r.status_code)
def accept_taa(agent_controller):
    response = await agent_controller.ledger.get_taa()
    TAA = response['result']['taa_record']
    TAA['mechanism'] = "service_agreement"
    response = await agent_controller.ledger.accept_taa(TAA)
    ## Will return {} if successful
    print(response)
def set_public_did(agent_controller,did_object):
    # Set the DID as public
    response = await agent_controller.wallet.assign_public_did(did_object["did"])
    print(response)
def get_public_did_and_verkey(agent_controller):
    # Get the public DID
    response = await agent_controller.wallet.get_public_did()
    print(response)
    issuer_nym = response['result']['did']
    print('\nIssuer public DID:',issuer_nym)
    # Get the verkey for the DID
    issuer_verkey = await agent_controller.ledger.get_did_verkey(issuer_nym)
    print(issuer_verkey)
    return issuer_nym, issuer_verkey
def get_public_did_endpoint(agent_controller,issuer_nym):
    # Get the endpoint for the DID
    issuer_endpoint = await agent_controller.ledger.get_endpoint_for_did(issuer_nym)
    return issuer_endpoint
def register_listener(agent_controller):
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(agent_controller.listen_webhooks())

    def cred_handler(payload):
        print("Handle Credentials")
        exchange_id = payload['credential_exchange_id']
        state = payload['state']
        role = payload['role']
        attributes = payload['credential_proposal_dict']['credential_proposal']['attributes']
        # print(f"Credential exchange {exchange_id}, role: {role}, state: {state}")
        # print(f"Offering: {attributes}")
    
    cred_listener = {
        "topic": "issue_credential",
        "handler": cred_handler
    }

    def connections_handler(payload):
        global STATE
        connection_id = payload["connection_id"]
        print("Connection message", payload, connection_id)
        STATE = payload['state']
        if STATE == 'active':
    #         print('Connection {0} changed state to active'.format(connection_id))
            print(colored("Connection {0} changed state to active".format(connection_id), "red", attrs=["bold"]))

    def proof_handler(payload):
        print("Handle present proof")
        print(payload)

    connection_listener = {
        "handler": connections_handler,
        "topic": "connections"
    }

    proof_listener = {
        "topic": "present_proof",
        "handler": proof_handler
    }

    agent_controller.register_listeners([cred_listener,connection_listener,proof_listener], defaults=True)

def write_schema_to_ledger(agent_controller, schema_name, schema_version, schema_attrs):
    # Write the schema to the ledger
    # attrs = ["name","age","skill"] for example
    schema_id, schema = await agent_controller.definitions.write_schema(schema_name, schema_version, schema_attrs)
    print(schema_id)
    print(schema)

def write_and_get_cred_def_to_ledger(agent_controller, schema_id):
    # Write the credential definition to the ledger
    cred_def_id = await agent_controller.definitions.write_cred_def(schema_id)
    print(cred_def_id)
    return cred_def_id

def send_credential_offer(agent_controller, cred_def_id, connection_id):
    record = await agent_controller.issuer.send_credential(connection_id, schema_id, cred_def_id, credential_attributes, trace=False)
    record_id = record['credential_exchange_id']
    state = record['state']
    role = record['role']
    print(f"Credential exchange {record_id}, role: {role}, state: {state}")

def gen_invitation(agent_controller):
    # Create an invitation
    invitation = await agent_controller.connections.create_invitation()
    print(invitation['invitation_url'])
    return invitation['invitation_url']
def gen_qrcode(invitation_url):
    # Generate a QR code
    import qrcode
    input_data = inviteURL
    # Creating an instance of qrcode
    qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=5)
    qr.add_data(input_data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img.save('issuer_agent_invite_QRcode.png')

    from IPython.display import Image
    Image(width=400, filename='./issuer_agent_invite_QRcode.png')
def check_connection(agent_controller,connection_id):
    import time

    print(colored("Current state for ConnectionId {} is {}".format(connection_id,STATE), "magenta", attrs=["bold"]))
    while STATE != 'active':
    #     print('ConnectionId {0} is not in active state yet'.format(connection_id))
        print(colored("ConnectionId {0} is not in active state yet".format(connection_id), "yellow", attrs=["bold"]))
        trust_ping = await agent_controller.messaging.trust_ping(connection_id,'hello!')
    #     print('Trust ping send to ConnectionId {0} to activate connection'.format(trust_ping))
        print(colored("Trust ping send to ConnectionId {0} to activate connection".format(trust_ping), "blue", attrs=["bold"]))
        time.sleep(5)
        
    # print('ConnectionId: {0} is now active. Continue with notebook'.format(connection_id))
    print(colored("ConnectionId: {0} is now active. Continue with notebook".format(connection_id), "green", attrs=["bold"]))

def gen_proof_request(agent_controller,schema_id,revocation=False,SELF_ATTESTED=True,exchange_tracing=False):
    
    #Enable this to ask for attributes to identity a user
    #TODO - change restriction according to schema
    req_attrs = [
        {"name": "fullname", "restrictions": [{"schema_id": schema_id}]},
        {"name": "skill", "restrictions": [{"schema_id": schema_id}]},
    ]

    #TODO - modify attrs to use custom attributes
    if revocation:
        req_attrs.append(
            {
                "name": "skill",
                "restrictions": [{"schema_id": schema_id}],
                "non_revoked": {"to": int(time.time() - 1)},
            },
        )

    if SELF_ATTESTED:
        # test self-attested claims
        req_attrs.append({"name": "country"},)

    #Set predicates for Zero Knowledge Proofs
    #TODO - modify to use custom predicates
    req_preds = [
        # test zero-knowledge proofs
        {
            "name": "age",
            "p_type": ">=",
            "p_value": 18,
            "restrictions": [{"schema_id": schema_id}],
        }
    ]

    indy_proof_request = {
        "name": "Proof of Completion of PyDentity SSI Tutorial",
        "version": "1.0",
        "requested_attributes": {
            f"0_{req_attr['name']}_uuid":
            req_attr for req_attr in req_attrs
        },
        "requested_predicates": {
            f"0_{req_pred['name']}_GE_uuid":
            req_pred for req_pred in req_preds
        },
    }

    if revocation:
        indy_proof_request["non_revoked"] = {"to": int(time.time())}

    #proof_request = indy_proof_request
    exchange_tracing_id = exchange_tracing
    proof_request_web_request = {
        "connection_id": connection_id,
        "proof_request": indy_proof_request,
        "trace": exchange_tracing,
    }
    return proof_request_web_request
def send_proof_request_and_get_id(agent_controller,proof_request_web_request):
    # Send the proof request
    proof_request_web_response = await agent_controller.proofs.send_request(proof_request_web_request)
    print(proof_request_web_response)
    proof_request_web_response_id = proof_request_web_response['presentation_exchange_id']
    return proof_request_web_response_id
def verify_proof(agent_controller,presentation_exchange_id):
    verify = await agent_controller.proofs.verify_presentation(presentation_exchange_id)
    print('verification state',verify['state'])
    for (name, val) in verify['presentation']['requested_proof']['revealed_attrs'].items():
        ## This is the actual data that you want. It's a little hidden
        print(val['raw'])
    for (name, val) in verify['presentation']['requested_proof']['self_attested_attrs'].items():
        print(name, val)