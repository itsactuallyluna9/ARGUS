import chromadb
import json

client = chromadb.HttpClient("localhost")
fact_checks = client.get_or_create_collection("fact_checks")

def clean_collection(col: chromadb.Collection) -> None:
    for id in col.get(ids=None)["ids"]:
        try:
            item = json.loads(col.get(ids=[id])['documents'][0])
            if item["finished"] == True:
                if "accuracy_explanation" in item and "completeness_explanation" in item and "political_bias" in item and "sensationalism" in item and "emotional_language" in item:
                    if item["accuracy_explanation"] == '' or item["completeness_explanation"] == '' or item["political_bias"] == '' or item["sensationalism"] == '' or item["emotional_language"] == '':
                        print(f"Deleting {id} because it is marked finished but has empty explanations")
                        col.delete(ids=[id])
                else:
                    print(f"Deleting {id} because it is marked finished but is missing some explanations")
                    col.delete(ids=[id])
        except Exception as e:
            print(f"Error processing item with id {id}: {e}")
            print(f"Deleting {id} because it is malformed")
            col.delete(ids=[id])
    

if __name__ == "__main__":
    clean_collection(fact_checks)