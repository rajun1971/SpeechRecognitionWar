import axios from 'axios'
import WebAudioL16Stream from 'web-audio-resampler'
import {createAudioMeter} from './volume-meter.js'

let localStream: MediaStream;
let connection: WebSocket;
let input: MediaStreamAudioSourceNode;
let processor: ScriptProcessorNode;
let session_id: any;
let speaking_flag = false;

const resampler = new WebAudioL16Stream();

const api_location = `${location.origin}/api/recognition`
const btn_start = document.getElementById("start") as HTMLInputElement;
const btn_stop = document.getElementById("stop") as HTMLInputElement;

let audioContext: AudioContext;

function getAudioContext() {
    if (audioContext === undefined) {
        audioContext = new ((<any>window).AudioContext || (<any>window).webkitAudioContext)();
    } 
    return audioContext;
}

function detectSilence(
    stream: MediaStream,
    onSoundEnd = () =>{},
    onSoundStart = () =>{},
    silence_delay = 500,
    min_decibels = -40
    ) {
    const ctx = getAudioContext();
    const analyser = ctx.createAnalyser();
    const streamNode = ctx.createMediaStreamSource(stream);
    streamNode.connect(analyser);
    analyser.minDecibels = min_decibels;

    const data = new Uint8Array(analyser.frequencyBinCount); // will hold our data
    let silence_start = performance.now();
    let triggered = false; // trigger only once per silence event

    function loop(time: number) {
        requestAnimationFrame(loop); // we'll loop every 60th of a second to check
        analyser.getByteFrequencyData(data); // get current data
        if (data.some(v => v > 0)) { // if there is data above the given db limit
            if(triggered){
                triggered = false;
                onSoundStart();
            }
            silence_start = time; // set it to now
        }
        if (!triggered && time - silence_start > silence_delay) {
            onSoundEnd();
            triggered = true;
        }
    }
    loop(0);
}

function dispLevelMeter(stream: MediaStream) {
    const canvas = document.getElementById("meter") as HTMLCanvasElement;
    const canvasContext = canvas.getContext("2d") as CanvasRenderingContext2D;
    const volumeElement = document.getElementById("volume") as HTMLElement;
    const fpsElement = document.getElementById("fps") as HTMLElement;
    const ctx = getAudioContext();
    const meter = createAudioMeter(ctx);
    const streamNode = ctx.createMediaStreamSource(stream);
    streamNode.connect(meter);
    let lastTime: number = 0;

    function loop(time: number){
        canvasContext.clearRect(0, 0, canvas.width, canvas.height);
        // check if we're currently clipping
        if (meter.checkClipping())
            canvasContext.fillStyle = "red";
        else
            canvasContext.fillStyle = "green";
        // draw a bar based on the current volume
        canvasContext.fillRect(0, 0, meter.volume*canvas.width*1.4, canvas.height);
        volumeElement.innerText = `${meter.volume}`;
        if(lastTime > 0) {
            fpsElement.innerText = `${time - lastTime}`;
        }
        lastTime = time;
        // set up the next visual callback
//        window.requestAnimationFrame(loop);
    }
//    window.requestAnimationFrame(loop);
    setInterval(loop, 100, 0);
}

function displayButton(isRecording: boolean) {
    btn_start.disabled = isRecording;
    btn_stop.disabled = !isRecording;
}

function onSilence() {
    console.log('silence');
    speaking_flag = false;
}

function onSpeak() {
    console.log('speaking');
    speaking_flag = true;
}

function setResult(data: string, disp_id: string) {
    const disp_element = document.getElementById(disp_id)
    if(data && disp_element) {
        disp_element.innerHTML = data;
    }
}

async function createSession() {
    const response = await axios.get(api_location);
    session_id = response.data.session_id;
    // WebSocketのコネクション
    const protocol = location.protocol === 'http:' ? 'ws:' : 'wss:';
    connection = new WebSocket(`${protocol}//${location.host}/api/recognition/${session_id}/websocket`);
    // サーバーからデータを受け取る
    connection.onmessage = (e) => {
        console.log(e.data);
        const data = JSON.parse(e.data);
        setResult(data.gcp, 'result_gcp');
        setResult(data.azure, 'result_azure');
        setResult(data.watson, 'result_watson');
        setResult(data.recaius, 'result_recaius');
    };
    localStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: false
    });
    dispLevelMeter(localStream);
    displayButton(false);
}

async function record() {
    displayButton(true);
    const response = await axios.get(`${api_location}/${session_id}/start`);
    const context = getAudioContext();
    input = context.createMediaStreamSource(localStream)
    processor = context.createScriptProcessor(1024, 1, 1);
    input.connect(processor);
    processor.connect(context.destination);
    processor.onaudioprocess = (e) => {
        const l16buffer = resampler.floatTo16BitPCM(resampler.downsample(e.inputBuffer.getChannelData(0)))
        connection.send(l16buffer.buffer); // websocketで送る
    };
};
async function stop() {
    displayButton(false);
    input.disconnect();
    processor.disconnect();
    await axios.get(`${api_location}/${session_id}/stop`);
}

var closeConnection = function() {
    connection.close();
}

if(btn_start && btn_stop) {
    btn_start.onclick = record;
    btn_stop.onclick = stop;
}

window.onload = createSession;
window.onunload = () => {
    localStream.getTracks().forEach((track: { stop: () => void; }) => track.stop());
    closeConnection();
}

/*
無音検出 : https://codeday.me/jp/qa/20190311/374489.html
*/
