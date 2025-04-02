import { createSignal, For, onMount, Show, type Component } from 'solid-js';

import { router } from './__generated_api_types__';
import styles from './App.module.css';
import { createMutable, createStore } from 'solid-js/store';






router['fuck-deprecated'].get({}).then((res) => console.log(`result: ${JSON.stringify(res)}`));
router.people[''].get({id: 4}).then((res) => console.log(`result: ${JSON.stringify(res)}`));




const [store, setStore] = createStore({});
const [serverSignals, setServerSignals] = createStore({});


const ws = new WebSocket('ws://localhost:8080/ws');

ws.onmessage = (event) => {
  console.log(event.data);
  const message = JSON.parse(event.data);
  console.log(message);
  switch (message.type) {
    case 'store-setValue':
      setStore(message['store'], message['key'], message['data']);
      break;
    case 'store-join':
      setStore(message['store'], message['data']);
      break;
    case 'toast':
      addToast(message['message']);
      break;
    case 'signal':
      setServerSignals(message['name'], message['value']);
      break;
  }
  };

const App: Component = () => {

  onMount(() => {
  });
  return (
    <div class={styles.App}>
      <Show when={serverSignals["playerCount"]}>
        <p>Players: {serverSignals["playerCount"]}</p>
      </Show>
      <Show when={store["people"]}>
        <People />
      </Show>
      <Toasts />
    </div>
  );
};




type Person = {
  id: number;
  name: string;
  age: number;
  parent: number | null;
  spouse: number | null;
  secret?: string;
}


function People() {
  return (
    <div>
      <Person_C person={(store["people"] as {[key: number]: Person})[1]} />
    </div>
  );
}


const profiles = [
  'https://img.freepik.com/premium-vector/avatar-profile-icon-flat-style-female-user-profile-vector-illustration-isolated-background-women-profile-sign-business-concept_157943-38866.jpg',
  'https://cdn-icons-png.flaticon.com/512/149/149071.png',
  'https://cdn3.pixelcut.app/7/18/profile_photo_maker_hero_100866f715.jpg',
  'https://img.freepik.com/premium-vector/avatar-profile-icon-flat-style-male-user-profile-vector-illustration-isolated-background-man-profile-sign-business-concept_157943-38764.jpg?semt=ais_hybrid',
  'https://newprofilepic.photo-cdn.net//assets/images/article/profile.jpg?90af0c8',
  'https://media.istockphoto.com/id/1437816897/photo/business-woman-manager-or-human-resources-portrait-for-career-success-company-we-are-hiring.jpg?s=612x612&w=0&k=20&c=tyLvtzutRh22j9GqSGI33Z4HpIwv9vL_MZw_xOE19NQ=',
  'https://buffer.com/library/content/images/2022/03/amina.png',
  'https://shmulisarmy.github.io/resume/images/profile.png',
  'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT2YaI6fNpee8j0XHI80Y7zt_4RvTygkXutIA&s',
]


const backendUrl = "http://localhost:8080";

function arrayIndex(arr: any[], index: number): any {
  return arr[index % arr.length];
}

type Toast = {
  message: string;
  id: number;
  startFadeOut: boolean;  

}

let toastId = 0;
const toasts = createMutable<{[id: number]: Toast}>({
});
function addToast(message: string) {
  const id = toastId++;
  toasts[id] = {message, id, startFadeOut: false};
  setTimeout(() => {
    toasts[id].startFadeOut = true;
    setTimeout(() => {
      delete toasts[id];
    }, 1000);
  }, 3000);
} 

function toQueryParams(params: Record<string, string>): string {
  return Object.entries(params).map(([key, value]) => `${key}=${value}`).join("&");
}

function Person_C(props: {person: Person}) {

  return (
    <div class='person' style={{display: "flex", "flex-direction": "column", "align-items": "center"}}>
      <div style={{position: "relative", padding: "8px 16px", width: "fit-content", display: "flex", "align-items": "center", gap: "10px", "border-radius": "10px", margin: "10px"}} class="profile">
        <img style={{width: "50px", height: "50px", "border-radius": "50%"}} src={arrayIndex(profiles, props.person.id)} alt="" />
        <div style={{"line-height": "8px", display: "flex", "flex-direction": "column", gap: "0px"}}>
          <EditableText text={props.person.name} onEdit={(name) => {
            const oldName = props.person.name;
            router.people.name.put({id: props.person.id, name: name}).then(() => {
              // already send out toasts in dbLiveStore
              // addToast(`updated ${oldName} to ${name}`);
            });
          }} />
          <p>{props.person.age}</p>
          <Show when={props.person.secret}>
            <span class='secret-tag' style={{"position": "absolute", "top": "0px", "right": "0px",
              "border": "1px solid lightgreen",
              "border-radius": "10px",  
              "border-bottom-left-radius": "0px",
              "padding": "8px 16px",
              "background-color": "black",
              "color": "white",
              "z-index": "1000"
            }}>{props.person.secret}</span>
          </Show>
        </div>
      </div>
      <div style={{display: "flex", "flex-direction": "row", "justify-content": "center", "align-items": "start", gap: "10px"}} class="children">
        <For each={Object.values(store["people"] as {[key: number]: Person}).filter(p => p.parent === props.person.id)}>
          {p => <Person_C person={p} />}
        </For>
      </div>
    </div>
  );
}

function EditableText(props: {text: string, onEdit: (text: string) => void}) {
  const[isEditing, setIsEditing] = createSignal(false);
  return (
    <Show when={isEditing()} fallback={<span style={{display: "block"}} onclick={() => setIsEditing(true)}>{props.text}</span>}>
      <input autofocus type="text" value={props.text} onchange={(e) => {props.onEdit(e.target.value); console.log("calling onEdit with " + e.target.value); setIsEditing(false)}} />
    </Show>
  );
}

function Toasts() {
  return (
    <div style={{
      "padding-top": "10px",
      "position": "absolute",
      "top": "0px",
      "right": "0px",
      "display": "flex",
      "flex-direction": "column",
      gap: "10px"
    }} class="toasts">
      <For each={Object.values(toasts)}>
        {toast => <Toast_c toast={toast} />}
      </For>
    </div>
  );
}

function Toast_c ({toast}: {toast: Toast}) { 
  return <div style={{
    "--slide-out-duration": "1s",
    background: "black",
    color: "white",
    padding: "8px 16px",
    "border-radius": "4px",
    "border": "1px solid lightgreen",
    "z-index": "1000",
    position: "relative",
    "display": "block"
  }} class={toast.startFadeOut ? "toast fade-out" : "toast"}>
    
    <span style={{
      position: "absolute",
      top: "-6px",
      left: "-6px",
      "z-index": "1001",
    }}>
<svg width="24" height="24" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle style={{ "animation": "draw 1s ease forwards 0.3s"}} cx="50" cy="50" r="40" stroke="green" stroke-width="8" fill="none"/>
    <path d="M30 50 L45 65 L70 35" stroke="green" stroke-width="8" fill="none" stroke-linecap="round" stroke-linejoin="round"
        stroke-dasharray="50"
        stroke-dashoffset="50"
        style={{"animation": "draw 1s ease forwards 0.3s"}} />
</svg>




</span>
    {toast.message}</div> };





export default App;
