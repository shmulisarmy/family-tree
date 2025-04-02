from collections import defaultdict


#utils
def infinite_dict():
    return defaultdict(infinite_dict)






ultra_router = infinite_dict()


def generate_ts_types(openapi_schema):
    ts_types = []
    ts_functions = []
    
    # Generate TypeScript interfaces from schemas
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        for name, schema in openapi_schema["components"]["schemas"].items():
            properties = schema.get("properties", {})
            required = set(schema.get("required", []))
            
            ts_types.append(f"export interface {name} {{")
            for prop_name, prop_info in properties.items():
                prop_type = "any"
                if "type" in prop_info:
                    if prop_info["type"] == "string":
                        prop_type = "string"
                    elif prop_info["type"] == "integer":
                        prop_type = "number"
                    elif prop_info["type"] == "array":
                        item_type = "any"
                        if "items" in prop_info:
                            if "$ref" in prop_info["items"]:
                                item_type = prop_info["items"]["$ref"].split("/")[-1]
                            elif "type" in prop_info["items"]:
                                item_type = prop_info["items"]["type"]
                        prop_type = f"{item_type}[]"
                
                optional = "" if prop_name in required else "?"
                ts_types.append(f"  {prop_name}{optional}: {prop_type};")
            ts_types.append("}")
    
    # Generate API functions
    for path, methods in openapi_schema["paths"].items():
        for method, details in methods.items():
            func_name = details["operationId"]
            
            request_body = details.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
            request_type = "any"
            if "$ref" in request_body:
                request_type = request_body["$ref"].split("/")[-1]
            
            ts_functions.append(f"export async function {func_name}(data: {request_type}): Promise<any> {{")
            ts_functions.append(f"  const response = await fetch('/{path}', {{")
            ts_functions.append(f"    method: '{method.upper()}',")
            ts_functions.append(f"    headers: {{ 'Content-Type': 'application/json' }},")
            ts_functions.append(f"    body: JSON.stringify(data)")
            ts_functions.append("  });")
            ts_functions.append("  return response.json();")
            ts_functions.append("}")
            
        current_route = ultra_router
        for segment in path.split("/")[1:]:
            current_route = current_route[segment]
        # current_route[method] = func_name
        current_route[method] = f"""createFetch<{request_type}>({f"{{method: '{method}', path: '{path}'}}"})"""

    ultra_router_string = f"""
    export const router = {dict_to_js_object(ultra_router)}
    """
    
    
    return "\n".join(["// API Types"] + ts_types + ["", "// API Router"] + [ultra_router_string])


def dict_to_js_object(d, depth=0):
    if not d:
        return "{}"
    indent = "  " * depth
    return "{\n" + indent + ",\n".join(map(lambda x: f"  '{x[0]}': {dict_to_js_object(x[1], depth+1) if isinstance(x[1], dict) else x[1]}", d.items())) + "}"


def place_ts_in_file(openapi_schema, port):
    ts_code = generate_ts_types(openapi_schema)


    js_utils = """
// API Utils
const baseUrl = 'http://localhost:""" + port + """';


function toQueryParams(params: Record<string, string>): string {
  return Object.entries(params).map(([key, value]) => `${key}=${value}`).join("&");
}

function createFetch<T>({method, path}: any): (data: T) => Promise<any> {
  return async function(data: T): Promise<any> {
    for (const route of path.split("/")) {
      if (route.startsWith("{") && route.endsWith("}")) {
        const param = route.slice(1, -1);
        path = path.replace(route, data[param]);
      }
    }
    const header = {
      method: method.toUpperCase(),
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    };
    if (method.toUpperCase() === 'GET') {
      delete header.body;
      path += `?${toQueryParams(data as Record<string, string> || {})}`;
    }
    console.log({path}, {data}, {method});
    const response = await fetch(`${baseUrl}${path}`, header);
    return response.json();
  }
}
"""
    
    with open("frontend/src/__generated_api_types__.ts", "w") as ts_file:
        ts_file.write(js_utils)
        ts_file.write(ts_code)



    print("TypeScript API client generated: api.ts")

