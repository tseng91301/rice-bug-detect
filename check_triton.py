import tritonclient.http as httpclient
try:
    client = httpclient.InferenceServerClient(url="trition.toolmen.bime.ntu.edu.tw")
    model_metadata = client.get_model_metadata(model_name="rice_bug_model")
    print("Metadata:", model_metadata)
    model_config = client.get_model_config(model_name="rice_bug_model")
    print("Config:", model_config)
except Exception as e:
    print("Error:", e)
