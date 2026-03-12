/**
 * AudioWorklet processor for seamless PCM audio streaming.
 * Based on pipecat-ai's stream_processor pattern.
 * Queues incoming Int16 PCM chunks and outputs them as continuous audio.
 */
class StreamProcessor extends AudioWorkletProcessor {
  constructor() {
    super()
    this.bufferQueue = []
    this.currentBuffer = null
    this.currentOffset = 0

    this.port.onmessage = (event) => {
      if (event.data.event === 'write') {
        const int16 = event.data.buffer
        const float32 = new Float32Array(int16.length)
        for (let i = 0; i < int16.length; i++) {
          float32[i] = int16[i] / 0x8000
        }
        this.bufferQueue.push(float32)
      } else if (event.data.event === 'clear') {
        this.bufferQueue = []
        this.currentBuffer = null
        this.currentOffset = 0
      }
    }
  }

  process(inputs, outputs) {
    const output = outputs[0][0]
    let outputOffset = 0

    while (outputOffset < output.length) {
      // Get next buffer if current is exhausted
      if (!this.currentBuffer || this.currentOffset >= this.currentBuffer.length) {
        if (this.bufferQueue.length === 0) {
          // Fill rest with silence
          for (let i = outputOffset; i < output.length; i++) {
            output[i] = 0
          }
          return true
        }
        this.currentBuffer = this.bufferQueue.shift()
        this.currentOffset = 0
      }

      // Copy samples from current buffer to output
      const remaining = this.currentBuffer.length - this.currentOffset
      const needed = output.length - outputOffset
      const toCopy = Math.min(remaining, needed)

      for (let i = 0; i < toCopy; i++) {
        output[outputOffset + i] = this.currentBuffer[this.currentOffset + i]
      }

      this.currentOffset += toCopy
      outputOffset += toCopy
    }

    return true
  }
}

registerProcessor('stream-processor', StreamProcessor)
