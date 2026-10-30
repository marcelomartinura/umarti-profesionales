<?php
// Recibe el formulario de /sumate/ y envía los datos por email para revisarlos.
// CONFIGURAR: casilla que recibe las solicitudes de ficha.
const DESTINO   = 'CAMBIAR@umartidigital.com';
const REMITENTE = 'no-responder@umartidigital.com';

function volver($ok) {
    header('Location: /sumate/?enviado=' . ($ok ? '1' : '0'), true, 303);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') volver(false);
if (!empty($_POST['sitio'])) volver(true);          // trampa para bots
if (($_POST['acepto'] ?? '') !== 'si') volver(false);

$campo = function ($k, $max = 120) {
    $v = trim((string)($_POST[$k] ?? ''));
    $v = str_replace(["\r", "\n", '"'], [' ', ' ', "'"], $v);
    return mb_substr($v, 0, $max);
};

$d = [
    'nombre'    => $campo('nombre', 80),
    'profesion' => $campo('profesion', 60),
    'categoria' => $campo('categoria', 60),
    'pais'      => $campo('pais', 40),
    'ciudad'    => $campo('ciudad', 60),
    'modalidad' => $campo('modalidad', 30),
    'anios'     => preg_replace('/\D/', '', $campo('anios', 3)),
    'bio'       => $campo('bio', 400),
    'whatsapp'  => $campo('whatsapp', 25),
    'email'     => filter_var(trim($_POST['email'] ?? ''), FILTER_VALIDATE_EMAIL) ?: '',
    'linkedin'  => filter_var(trim($_POST['linkedin'] ?? ''), FILTER_VALIDATE_URL) ?: '',
    'web'       => filter_var(trim($_POST['web'] ?? ''), FILTER_VALIDATE_URL) ?: '',
];
$servicios = array_slice(array_filter(array_map(
    fn($s) => mb_substr(trim(str_replace('"', "'", $s)), 0, 90),
    preg_split('/\r?\n/', (string)($_POST['servicios'] ?? ''))
)), 0, 5);

if ($d['nombre'] === '' || $d['profesion'] === '' || $d['ciudad'] === '' || $d['bio'] === '' || $d['email'] === '' || !$servicios) {
    volver(false);
}

// Línea lista para pegar en data/profesionales.csv
$fila = implode(',', array_map(fn($v) => '"' . $v . '"', [
    '', 'no', $d['nombre'], $d['profesion'], $d['categoria'], $d['pais'], $d['ciudad'], $d['modalidad'],
    $d['anios'], $d['bio'], implode('|', $servicios), $d['whatsapp'], $d['email'], $d['linkedin'], $d['web'],
]));

$cuerpo = "Nueva solicitud de ficha en Umarti Profesionales\n\n";
foreach ($d as $k => $v) $cuerpo .= ucfirst($k) . ": $v\n";
$cuerpo .= "Servicios:\n- " . implode("\n- ", $servicios) . "\n\nFila para el CSV:\n$fila\n";

$asunto = "Nueva ficha: {$d['nombre']} ({$d['profesion']}, {$d['pais']})";
$cabeceras = "From: Umarti Profesionales <" . REMITENTE . ">\r\n"
           . "Reply-To: {$d['email']}\r\n"
           . "Content-Type: text/plain; charset=UTF-8\r\n";

volver(mail(DESTINO, '=?UTF-8?B?' . base64_encode($asunto) . '?=', $cuerpo, $cabeceras));
