imageBlock = """
<div class="masonry-item">
    <a href="{{media_path}}" onclick="copyToClipboard('{{hash}}'); event.preventDefault();">
        <img src="{{media_path}}" alt="{{hash}}" loading="lazy">
    </a>
</div>
"""

videoBlock = """
<div class="masonry-item">
    <video width="300" controls>
        <source src="{{uploaded_url}}" type="video/mp4" loading="lazy">
        Your browser does not support the video tag. {{hashVal}}
    </video>
</div>
"""

