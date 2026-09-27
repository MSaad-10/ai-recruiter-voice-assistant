import * as VapiModule from "@vapi-ai/web";
import "./style.css";

const Vapi =
    VapiModule.default?.default ??
    VapiModule.default ??
    VapiModule;

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const VAPI_PUBLIC_KEY = import.meta.env.VITE_VAPI_PUBLIC_KEY;

const vapi = new Vapi(VAPI_PUBLIC_KEY);


let currentLocalCallId = null;
let currentVapiCallId = null;


const candidateIdInput = document.querySelector("#candidate-id");
const startButton = document.querySelector("#start-button");
const endButton = document.querySelector("#end-button");
const statusElement = document.querySelector("#status");


function setStatus(status) {
    statusElement.textContent = status;
}


async function createLocalVoiceSession(candidateId) {
    const response = await fetch(
        `${API_BASE_URL}/voice-sessions/start`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                candidate_id: candidateId,
            }),
        }
    );


    if (!response.ok) {
        const errorData = await response.json();

        throw new Error(
            errorData.detail || "Unable to create voice session"
        );
    }


    return response.json();
}


async function linkVapiCall(
    localCallId,
    vapiCallId
) {
    const response = await fetch(
        `${API_BASE_URL}/voice-sessions/${localCallId}/vapi-call`,
        {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                vapi_call_id: vapiCallId,
            }),
        }
    );

    if (!response.ok) {
        throw new Error(
            "Unable to link Vapi call with local session"
        );
    }

    return response.json();
}


async function startInterview() {
    try {
        const candidateId = Number(candidateIdInput.value);


        if (!candidateId) {
            setStatus("Please enter a valid candidate ID.");
            return;
        }


        startButton.disabled = true;

        setStatus("Checking microphone...");

        await verifyMicrophoneAccess();

        setStatus("Preparing interview...")

        const session = await createLocalVoiceSession(candidateId);


        currentLocalCallId = session.local_call_id;

        const assistantOverrides = {
            variableValues: {
                candidate_id: String(session.candidate_id),
                call_id: String(session.local_call_id),
                candidate_name: session.candidate_name,
            },
        };

        setStatus("Connecting to recruiter...");

        const call = await vapi.start(
            undefined,
            assistantOverrides,
            session.squad_id
        );

        console.log("Vapi start result:", call);

        if (call?.id) {
            currentVapiCallId = call.id;

            await linkVapiCall(
                currentLocalCallId,
                currentVapiCallId
            );
        }

    } catch (error) {
        console.error(error);

        setStatus(`Error: ${error.message}`);

        startButton.disabled = false;
    }
}


async function verifyMicrophoneAccess() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: true,
        });

        const audioTracks = stream.getAudioTracks();

        console.log("Microphone tracks:", audioTracks);

        if (audioTracks.length === 0) {
            throw new Error("No microphone audio track found.");
        }

        const track = audioTracks[0];

        console.log("Microphone label:", track.label);
        console.log("Microphone enabled:", track.enabled);
        console.log("Microphone muted:", track.muted);
        console.log("Microphone ready state:", track.readyState);

        stream.getTracks().forEach((track) => track.stop());

        return true;

    } catch (error) {
        console.error("Microphone test failed:", error);
        throw new Error(
            "Microphone access failed. Check browser and Windows permissions."
        );
    }
}



function endInterview() {
    vapi.stop();
}


vapi.on("call-start", () => {
    setStatus("Interview connected");

    startButton.disabled = true;
    endButton.disabled = false;
});


vapi.on("call-end", () => {
    setStatus("Interview ended");

    startButton.disabled = false;
    endButton.disabled = true;

    currentVapiCallId = null;
});


vapi.on("error", (error) => {
    console.error("Vapi error:", error);

    setStatus("Voice connection error");

    startButton.disabled = false;
    endButton.disabled = true;
});


startButton.addEventListener(
    "click",
    startInterview
);


endButton.addEventListener(
    "click",
    endInterview
);


