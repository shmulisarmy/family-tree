
// API Utils
const baseUrl = 'http://localhost:8080';


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
// API Types
export interface HTTPValidationError {
  detail?: ValidationError[];
}
export interface Person {
  id: number;
  name: string;
  parent?: any;
  secret?: any;
  last_updated?: any;
}
export interface UpdateNamePayload {
  id: number;
  name: string;
}
export interface ValidationError {
  loc: any[];
  msg: string;
  type: string;
}

// API Router

    export const router = {
  'docs2': {
    'get': createFetch<any>({method: 'get', path: '/docs2'})},
  'fuck-deprecated': {
    'get': createFetch<any>({method: 'get', path: '/fuck-deprecated'})},
  'people': {
    'name': {
      'put': createFetch<UpdateNamePayload>({method: 'put', path: '/people/name'})},
  '': {
      'get': createFetch<any>({method: 'get', path: '/people/'})}},
  '': {
    'get': createFetch<any>({method: 'get', path: '/'})}}
    