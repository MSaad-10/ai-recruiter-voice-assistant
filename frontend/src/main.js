import Vapi from "@vapi-ai/web";
import "./style.css";


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

        setStatus("Preparing interview...");


        const session = await createLocalVoiceSession(candidateId);


        currentLocalCallId = session.local_call_id;


        setStatus("Connecting to recruiter...");


        const call = await vapi.start(
            undefined,
            undefined,
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


