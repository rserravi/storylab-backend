# StoryLab Backend

## AI and Media Endpoints

Los endpoints que generan contenido aceptan ahora un campo `project_id` para asociar los resultados con un proyecto específico.

### Endpoints afectados

- `POST /ai/treatment`
- `POST /ai/turning-points`
- `POST /ai/character`
- `POST /ai/location`
- `POST /ai/scene`
- `POST /ai/dialogue/polish`
- `POST /ai/review`
- `POST /ai/image`

### Ejemplo de solicitud

```json
POST /ai/treatment
{
  "project_id": "123",
  "logline": "Un ejemplo de logline",
  "tone": "cinematográfico"
}
```

```json
POST /ai/image
{
  "project_id": "123",
  "prompt": "Atardecer en la montaña",
  "style": "fast"
}
```

