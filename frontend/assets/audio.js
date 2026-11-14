/* Quiet, synthesized audio: no downloads, microphone, or autoplay. */
globalThis.MathBlitzAudio = (() => {
  let context;
  let music;
  let beat;
  let step = 0;
  let enabled = false;
  const motifs = {
    start: [440, 554.37], correct: [523.25, 659.25, 783.99],
    incorrect: [440, 349.23], timeout: [392],
  };

  async function unlock() {
    try {
      const Audio = globalThis.AudioContext || globalThis.webkitAudioContext;
      if (!Audio) return false;
      context ||= new Audio();
      if (context.state !== "running") await context.resume();
      return context.state === "running";
    } catch { return false; }
  }

  function note(frequency, time, length, gain, output) {
    const oscillator = context.createOscillator();
    const envelope = context.createGain();
    oscillator.type = "sine";
    oscillator.frequency.value = frequency;
    envelope.gain.setValueAtTime(0.0001, time);
    envelope.gain.exponentialRampToValueAtTime(gain, time + 0.035);
    envelope.gain.exponentialRampToValueAtTime(0.0001, time + length);
    oscillator.connect(envelope).connect(output);
    oscillator.start(time);
    oscillator.stop(time + length + 0.02);
    oscillator.onended = () => { oscillator.disconnect(); envelope.disconnect(); };
  }

  function play(name) {
    if (context?.state !== "running" || document.hidden) return;
    motifs[name]?.forEach((frequency, index) => note(frequency, context.currentTime + index * 0.085, 0.18, 0.085, context.destination));
  }

  function stop() {
    clearInterval(beat);
    if (music) { music.disconnect(); music = null; }
  }

  function start() {
    if (!enabled || document.hidden || music || context?.state !== "running") return;
    music = context.createGain();
    music.gain.value = 0.2;
    music.connect(context.destination);
    const chords = [[130.81, 196, 261.63], [110, 164.81, 261.63], [87.31, 130.81, 220], [98, 146.83, 246.94]];
    const pulse = () => {
      const chord = chords[Math.floor(step / 4) % chords.length];
      note(chord[step % 3], context.currentTime, 0.85, 0.12, music);
      if (step % 4 === 0) note(chord[0] / 2, context.currentTime, 1.4, 0.1, music);
      step++;
    };
    pulse();
    beat = setInterval(pulse, 650);
  }

  async function setMusic(value) {
    enabled = value;
    if (!enabled) stop();
    else if (await unlock()) start();
    else enabled = false;
    return enabled;
  }

  document.addEventListener("visibilitychange", () => document.hidden ? stop() : start());
  return { unlock, play, setMusic };
})();
