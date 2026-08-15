import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.api.main import app

def export_openapi():
    print("Generating openapi.json...")
    openapi_data = app.openapi()
    
    docs_dir = BASE_DIR / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    out_path = docs_dir / "openapi.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(openapi_data, f, indent=2)
    print(f"Saved: {out_path}")
    return openapi_data

def generate_postman_collection(openapi_data):
    print("Generating Postman collection...")
    
    # Base collection structure (Postman Collection Schema v2.1.0)
    collection = {
        "info": {
            "name": "N100 Financial Intelligence API",
            "_postman_id": "n100-financial-intelligence-api-collection",
            "description": "API collection for Nifty 100 Financial Intelligence Platform REST endpoints.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": []
    }
    
    # We can group endpoints by tags from OpenAPI or just list them
    # To keep it clean, let's group by tags
    tag_folders = {}
    
    paths = openapi_data.get("paths", {})
    for path_str, methods in paths.items():
        for method_str, details in methods.items():
            # Skip if it is a documentation/internal route
            if path_str in ("/openapi.json", "/docs", "/redoc"):
                continue
                
            tags = details.get("tags", ["General"])
            tag_name = tags[0]
            
            if tag_name not in tag_folders:
                tag_folders[tag_name] = {
                    "name": tag_name,
                    "item": []
                }
                
            # Parse parameters to build a sample URL path
            # Replace path parameters like {ticker} with a placeholder or sample
            path_segments = [seg for seg in path_str.split("/") if seg]
            
            # Map parameters
            parameters = details.get("parameters", [])
            query_params = []
            for param in parameters:
                if param.get("in") == "query":
                    query_params.append({
                        "key": param.get("name"),
                        "value": "",
                        "description": param.get("description", "")
                    })
            
            item_name = details.get("summary") or details.get("operationId") or f"{method_str.upper()} {path_str}"
            description = details.get("description", "")
            
            # Build request structure
            request_item = {
                "name": item_name,
                "request": {
                    "method": method_str.upper(),
                    "header": [],
                    "url": {
                        "raw": f"http://localhost:8000/{'/'.join(path_segments)}",
                        "protocol": "http",
                        "host": ["localhost"],
                        "port": "8000",
                        "path": path_segments
                    },
                    "description": description
                }
            }
            
            if query_params:
                request_item["request"]["url"]["query"] = query_params
                # Reconstruct raw url with query params
                query_str = "&".join([f"{q['key']}={q['value']}" for q in query_params])
                request_item["request"]["url"]["raw"] += f"?{query_str}"
                
            # If POST/PUT with a request body, include it
            request_body = details.get("requestBody")
            if request_body:
                content = request_body.get("content", {})
                json_schema = content.get("application/json", {})
                # We can add a placeholder body for the request
                request_item["request"]["body"] = {
                    "mode": "raw",
                    "raw": "{\n  \"allocations\": {\n    \"TCS\": 0.6,\n    \"INFY\": 0.4\n  },\n  \"risk_free_rate\": 7.0\n}",
                    "options": {
                        "raw": {
                            "language": "json"
                        }
                    }
                }
                request_item["request"]["header"].append({
                    "key": "Content-Type",
                    "value": "application/json"
                })
            
            tag_folders[tag_name]["item"].append(request_item)
            
    # Add folders to collection
    for folder in sorted(tag_folders.values(), key=lambda x: x["name"]):
        collection["item"].append(folder)
        
    out_path = BASE_DIR / "docs" / "n100_api.postman_collection.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(collection, f, indent=2)
    print(f"Saved: {out_path}")

def main():
    openapi_data = export_openapi()
    generate_postman_collection(openapi_data)

if __name__ == "__main__":
    main()
