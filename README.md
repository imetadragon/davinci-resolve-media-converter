# DaVinci Resolve Media Converter (Linux)

![Ekran Görüntüsü](sample.png)

[English](#english) | [Türkçe](#türkçe) 


<a name="english"></a>

A practical GUI media converter for AAC audio codecs and h264/5 video codecs that are not supported in the Free or Studio versions of DaVinci Resolve on Linux.

For the Free version, it is recommended to convert using the MPEG-4 mode with the **Re-encode Video** option.

Although DaVinci Resolve Studio supports h264/5 codecs, it does not support the AAC audio codec. Therefore, you can convert AAC to PCM in seconds using the **Audio Only** mode.

## Prerequisites & Dependencies

This application requires **FFmpeg** to be installed on your system to perform media conversions. You can install it via your distribution's package manager:

- **Ubuntu / Debian:** `sudo apt install ffmpeg`
- **Fedora:** `sudo dnf install ffmpeg`
- **Arch Linux:** `sudo pacman -S ffmpeg`

## Features
- Outputs are stored under the **./output** directory located in the same directory as the video.

- Multiple Codec Options: MPEG-4, DNxHR LB, and DNxHR HQ modes.

- Drag & Drop Support: Ability to drop files directly into the interface.

- Batch Conversion: Queue and process multiple media files simultaneously.

- Smart Memory (QSettings): Remembers last selected settings and interface language.


---

<a name="türkçe"></a>

Linux'ta DaVinci Resolve Ücretsiz veya Stüdyo versiyonunda desteklenmeyen AAC ses kodeği ve h264/5 video kodekleri için pratik bir grafik arayüzlü dönüştürücü.

Ücretsiz sürüm için **Videoyu yeniden kodla** seçeneğiyle MPEG-4 modunda dönüştürmeniz önerilir.

DaVinci Resolve Studio versiyonu h264/5 kodeklerini desteklese de AAC ses kodeğini desteklemiyor. Bu yüzden **Yalnızca Ses** modu ile AAC'yi PCM'e saniyeler içinde çevirebilirsiniz.


## Gereksinimler ve Bağımlılıklar

Uygulamanın medya dönüştürme işlemlerini gerçekleştirebilmesi için sisteminizde **FFmpeg** aracının kurulu olması gerekir. Kullandığınız dağıtımın paket yöneticisi ile kolayca kurabilirsiniz:

- **Ubuntu / Debian:** `sudo apt install ffmpeg`
- **Fedora:** `sudo dnf install ffmpeg`
- **Arch Linux:** `sudo pacman -S ffmpeg`

## Özellikler
- Çıktılar videonun bulunduğu dizinde **./output** dizini altına depolanır.

- Video için çoklu codec Seçenekleri: MPEG-4, DNxHR LB ve DNxHR HQ modları.

- Sürükle-Bırak Desteği: Dosyaları doğrudan arayüze bırakabilme.

- Toplu Dönüştürme: Aynı anda birden fazla medyayı kuyruğa alıp işleme.

- Akıllı Hafıza (QSettings): Son seçilen ayarları ve arayüz dilini hatırlar.
