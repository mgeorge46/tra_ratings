/* static/rating/voice_rating.js */
// Submit the form — server will take you to confirmation page
voiceModeField.value = '1';
const form = document.forms[0];
if (form) form.submit();
state = STATE.IDLE;
return;
}
if (/start over|restart|edit|change/i.test(t)) {
resetFlow(true);
return;
}
speak('Please say Submit to continue, or Start over to restart.');
break;
}
}
}


function summarizeAndConfirm() {
const plate = numberPlateField ? numberPlateField.value : '';
const score = scoreField ? scoreField.value : '';
const reasons = systemCommentsField ? systemCommentsField.value : '';
const summary = `You are rating plate ${plate}, with ${score} stars, because: ${reasons}. Say Submit to continue or Start over to restart.`;
speak(summary);
state = STATE.AWAIT_CONFIRM;
// ensure UI button enabled if all fields are ok
if (rateButton) rateButton.disabled = false;
}


function resetFlow(announce) {
if (announce) speak('Okay, starting over. Which vehicle type would you like to rate?');
selectedOptionIdxs = [];
currentOptions = [];
if (systemCommentsField) systemCommentsField.value = '';
if (otherCommentField) { otherCommentField.value = ''; otherCommentField.style.display = 'none'; otherCommentField.required = false; }
if (scoreField) scoreField.value = '';
if (numberPlateField) numberPlateField.value = '';
state = STATE.AWAIT_TYPE;
}


// ---- Public controls ----
function initVoiceUI() {
const container = document.getElementById('voiceControls') || (function(){
const c = document.createElement('div');
c.id = 'voiceControls';
c.className = 'voice-controls';
(document.querySelector('.rating-card') || document.body).prepend(c);
return c;
})();


container.innerHTML = `
<div class="flex items-center gap-2">
<button type="button" id="voiceToggle" class="btn btn-secondary">🎙️ Start voice</button>
<label>
Accent:
<select id="voiceLang">
<option value="en-GB">English (UK)</option>
<option value="en-KE">English (Kenya)</option>
<option value="en-NG">English (Nigeria)</option>
<option value="en-ZA">English (South Africa)</option>
<option value="en-US">English (US)</option>
</select>
</label>
<span id="voiceStatus" class="ml-2 text-sm"></span>
</div>`;


const toggle = $('#voiceToggle');
const status = $('#voiceStatus');
const langSel = $('#voiceLang');


if (!HAS_SPEECH) {
toggle.disabled = true;
status.textContent = 'Voice not supported on this device.';
return;
}


langSel.value = localStorage.getItem('voice_lang') || 'en-GB';
langSel.addEventListener('change', () => {
localStorage.setItem('voice_lang', langSel.value);
if (rec) rec.lang = langSel.value;
});


toggle.addEventListener('click', () => {
if (state === STATE.IDLE) {
status.textContent = 'Listening for the wake word: "Rating"';
startRecognizer();
state = STATE.IDLE; // make sure
speak('Voice is ready. Say: Rating.');
toggle.textContent = '🛑 Stop voice';
} else {
status.textContent = 'Voice stopped';
stopRecognizer();
rec = null; state = STATE.IDLE;
toggle.textContent = '🎙️ Start voice';
window.speechSynthesis.cancel();
}
});
}


document.addEventListener('DOMContentLoaded', initVoiceUI);
})();