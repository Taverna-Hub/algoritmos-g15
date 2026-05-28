export const formatFrequencyHz = (frequency?: number) => {
  if (frequency == null) return '-'

  const frequencyHz = frequency < 1000000 ? frequency * 1000000 : frequency
  return `${frequencyHz.toLocaleString('pt-BR')} Hz`
}
